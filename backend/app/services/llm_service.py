import json
import httpx
import pandas as pd
from typing import Dict, List, Any
from app.schemas.analysis import InnovationBlueprintItem
from app.schemas.insight import InsightResponse
from app.core.config import settings


# ═══════════════════════════════════════════════════════════════════
# FUNGSI UTAMA – dipanggil oleh endpoint /analyze
# ═══════════════════════════════════════════════════════════════════

def _sanitize_price_ceiling(item):
    """Perbaiki competitor_price_ceiling yang tidak wajar TANPA membuang
    seluruh item. Ditemukan lewat testing: model konsisten (6 dari 6 kasus
    di 3 percobaan nyata) menghasilkan ceiling 4-14x lipat dari
    recommended_price untuk skenario 'belum ada kecocokan tren' -- padahal
    teks justifikasi & whatsapp_copy_text-nya sendiri sudah benar dan
    spesifik. Menolak seluruh item karena 1 angka yang meleset itu boros --
    cukup angkanya saja yang dikoreksi ke rentang wajar (maks 1.3x)."""
    price = item.get("recommended_price")
    ceiling = item.get("competitor_price_ceiling")
    if price and price > 0:
        if not ceiling or ceiling <= 0 or ceiling / price > 1.5:
            item["competitor_price_ceiling"] = int(price * 1.3)
    return item


def _validate_blueprint_grounding(items, actual_products, target):
    """Cek dasar: blueprint dari LLM harus merujuk produk & lokasi yang
    BENERAN ada di prompt -- kalau tidak, itu tanda model overfit/salah
    baca konteks (nyasar ke contoh training, bukan menjawab prompt yang
    sebenarnya diberikan). Perbaikan harga ditangani terpisah lewat
    _sanitize_price_ceiling() SEBELUM fungsi ini dipanggil -- di sini cuma
    cek recommended_price valid (bukan nol/negatif), bukan rasio ke ceiling."""
    if not items:
        return False
    for item in items:
        if item.get("target_location") != target:
            return False

        text = (item.get("title", "") + " " + item.get("justification", "")).lower()
        mentioned = any(
            any(word.lower() in text for word in p.split() if len(word) > 3)
            for p in actual_products
        )
        if not mentioned:
            return False

        price = item.get("recommended_price")
        if not price or price <= 0:
            return False
    return True


def generate_innovation_blueprint(
    cleaned_data: pd.DataFrame,
    data_health: Dict[str, Any],
    correlation_metrics: Dict[str, Any],
    target_lokasi: str
) -> List[InnovationBlueprintItem]:
    """
    Membangun prompt dari data kesehatan & korelasi, memanggil LLM
    (Ollama lokal via httpx sinkron), dan mengembalikan blueprint inovasi.
    Jika LLM tidak tersedia ATAU jawabannya tidak nyambung dengan prompt
    (gagal validasi grounding) -> fallback ke simulasi cerdas.
    """
    # 1. Bangun prompt
    prompt = _build_prompt(cleaned_data, data_health, correlation_metrics, target_lokasi)

    # 2. Coba panggil Ollama
    try:
        llm_json = _call_ollama(prompt)
        print(f"[LLM RAW RESPONSE] {llm_json}")

        items = _parse_llm_response(llm_json, target_lokasi)  # sekarang list of dict
        print(f"[LLM PARSED] {len(items) if items else 0} item(s)")

        if items:
            items = [_sanitize_price_ceiling(item) for item in items]  # kerja di dict, gak berubah
        actual_products = cleaned_data["product_name"].dropna().tolist()

        if items:
            grounded = _validate_blueprint_grounding(items, actual_products, target_lokasi)  # kerja di dict, gak berubah
            print(f"[GROUNDING CHECK] valid={grounded} | expected_products={actual_products} | expected_location={target_lokasi}")
            if grounded:
                return [InnovationBlueprintItem(**i) for i in items]  # konversi balik ke Pydantic di sini
        else:
            print("[LLM FALLBACK] items kosong setelah parsing -- kemungkinan _parse_llm_response gagal baca format JSON")

    except Exception as e:
        print(f"[LLM FALLBACK TRIGGERED - EXCEPTION] {type(e).__name__}: {e}")
        return _simulate_blueprint(cleaned_data, correlation_metrics, target_lokasi)

    print("[LLM FALLBACK] grounding validation gagal, jatuh ke simulasi")
    return _simulate_blueprint(cleaned_data, correlation_metrics, target_lokasi)


# ═══════════════════════════════════════════════════════════════════
# PEMBANGUN PROMPT
# ═══════════════════════════════════════════════════════════════════

def _build_prompt(
    df: pd.DataFrame,
    health: Dict[str, Any],
    corr: Dict[str, Any],
    target: str
) -> str:
    """Membuat prompt natural language dari data terstruktur."""

    # Ringkasan kesehatan data
    reliability = health.get("reliability_score", 0)
    status = health.get("status_color", "red")
    warnings = health.get("warning_message", "Tidak ada")

    # Ringkasan produk dari DataFrame
    product_list = []
    for _, row in df.head(10).iterrows():
        name = row.get("product_name", "Unknown")
        # PENTING: row.get("qty_sold", 0) TIDAK cukup -- default cuma dipakai
        # kalau key hilang total, bukan kalau nilainya ADA tapi NaN (dan NaN
        # memang skenario yang sengaja didesain muncul dari csv_parser.py
        # untuk baris data yang rusak -- ini bug yang sama persis dengan
        # yang sudah diperbaiki di analyze.py, sekarang muncul lagi di sini).
        qty_raw = row.get("qty_sold")
        stock_raw = row.get("remaining_stock")
        price_raw = row.get("unit_price")
        qty = int(qty_raw) if pd.notna(qty_raw) else 0
        stock = int(stock_raw) if pd.notna(stock_raw) else 0
        price = price_raw if pd.notna(price_raw) else 0
        product_list.append(f"- {name}: terjual {qty}, stok {stock}, harga {price}")

    # Detail korelasi per produk (jika ada)
    per_product = corr.get("per_product_details", [])
    if per_product:
        corr_lines = []
        for p in per_product:
            kw = p.get("keyword_overlap_score", 0)
            seg = p.get("matched_segment", "tidak diketahui")
            price_score = p.get("price_competitiveness_score")
            if price_score is not None:
                price_str = f"skor kompetitif harga {price_score:.2f}"
            else:
                price_str = "data kompetitor tidak tersedia"
            corr_lines.append(f"- {p['product_name']}: keyword overlap {kw:.2f} (segmen: {seg}), {price_str}")
        corr_text = "\n".join(corr_lines)
    else:
        corr_text = "Data korelasi detail tidak tersedia."

    # Gabungkan prompt
    return f"""
        Kamu adalah AI Business Advisor senior untuk UMKM. Berikan rekomendasi inovasi produk berdasarkan data penjualan dan pasar berikut.

        ### KESEHATAN DATA
        Skor Keandalan: {reliability}/100 (status: {status})
        Catatan: {warnings}

        ### PRODUK (dari CSV)
        {chr(10).join(product_list) if product_list else 'Tidak ada produk'}

        ### KORELASI PASAR (target: {target})
        {corr_text}

        ### INSTRUKSI
        Berdasarkan data di atas, berikan 2-3 ide inovasi produk (Hyper-Local atau Dead-Stock Resurrection) untuk target lokasi {target}.
        Output HARUS dalam format JSON array dengan struktur:
        [
        {{
            "id": "inv-001",
            "title": "Judul Inovasi",
            "target_location": "{target}",
            "recommended_price": 25000,
            "competitor_price_ceiling": 30000,
            "justification": "Alasan berdasarkan data",
            "risk_factors": ["risiko 1", "risiko 2"],
            "whatsapp_copy_text": "Teks promosi siap salin untuk WA Business"
        }}
        ]
        HANYA kembalikan JSON array, tanpa teks tambahan.
        """


# ═══════════════════════════════════════════════════════════════════
# PANGGILAN OLLAMA (via httpx sinkron)
# ═══════════════════════════════════════════════════════════════════

def _call_ollama(prompt: str) -> dict:
    """Mengirim prompt ke Ollama API secara sinkron dengan httpx."""
    with httpx.Client(timeout=300.0) as client:  # naik dari 90 -> 300 detik
        resp = client.post(
            settings.LLM_ENDPOINT,
            json={
                "model": settings.LLM_MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
        )
        resp.raise_for_status()
        data = resp.json()
        llm_output = data.get("response", "[]").strip()

        if llm_output.startswith("```"):
            llm_output = llm_output.split("\n", 1)[-1].rsplit("\n", 1)[0]

        return json.loads(llm_output)

def _parse_llm_response(llm_json: Any, target: str) -> List[dict]:
    """Validasi dan konversi response LLM ke list dict yang sudah tervalidasi skema."""
    if isinstance(llm_json, dict) and "data" in llm_json:
        llm_json = llm_json["data"]

    if not isinstance(llm_json, list):
        return []

    items = []
    for item in llm_json:
        try:
            item["target_location"] = target
            validated = InnovationBlueprintItem(**item)  # validasi skema tetap jalan
            items.append(validated.model_dump())  # tapi disimpan sebagai dict
        except Exception:
            continue
    return items[:3]


# ═══════════════════════════════════════════════════════════════════
# FALLBACK SIMULASI CERDAS (tanpa LLM)
# ═══════════════════════════════════════════════════════════════════

def _simulate_blueprint(
    df: pd.DataFrame,
    corr: Dict[str, Any],
    target: str
) -> List[InnovationBlueprintItem]:
    """Menghasilkan blueprint secara deterministik dari data yang ada."""

    items = []
    per_product = corr.get("per_product_details", [])
    if per_product is None:
        per_product = []

    # Ambil maksimal 2 produk dengan skor overlap tertinggi
    sorted_prods = sorted(per_product, key=lambda x: x.get("keyword_overlap_score", 0), reverse=True)
    for i, prod in enumerate(sorted_prods[:2]):
        name = prod.get("product_name", "Produk")
        overlap = prod.get("keyword_overlap_score", 0)
        seg = prod.get("matched_segment", "pasar lokal")
        price = prod.get("user_price", 0) or 20000
        comp_price = prod.get("avg_competitor_price", price * 1.2)
        id_str = f"inv-{i+1:03d}"

        if overlap > 0.5:
            justification = f"Korelasi tinggi ({overlap:.0%}) dengan segmen '{seg}'. Harga kompetitif dibanding kompetitor rata-rata {comp_price:.0f}."
        else:
            justification = f"Potensi dead-stock resurrection: produk '{name}' dapat dipasarkan ulang ke segmen {seg} dengan penyesuaian."

        items.append(InnovationBlueprintItem(
            id=id_str,
            title=f"Inovasi {name} untuk {target}",
            target_location=target,
            recommended_price=int(price * 0.9),
            competitor_price_ceiling=int(comp_price),
            justification=justification,
            risk_factors=["Respons pasar perlu diuji", "Ketersediaan bahan baku"],
            whatsapp_copy_text=f"Coba {name} edisi spesial {target}! Lebih terjangkau, lebih cocok buat kamu. 🔥"
        ))

    # Jika tidak ada produk dari korelasi, fallback ke DataFrame
    if not items and not df.empty:
        row = df.iloc[0]
        name = row.get("product_name", "Produk Unggulan")
        items.append(InnovationBlueprintItem(
            id="inv-001",
            title=f"Optimasi {name} untuk {target}",
            target_location=target,
            recommended_price=20000,
            competitor_price_ceiling=25000,
            justification="Berdasarkan data penjualan dan potensi pasar lokal.",
            risk_factors=["Data kompetitor terbatas"],
            whatsapp_copy_text=f"Jangan lewatkan {name} edisi {target}! 🌟"
        ))

    return items


# ═══════════════════════════════════════════════════════════════════
# FUNGSI UNTUK ENDPOINT /insight/generate
# ═══════════════════════════════════════════════════════════════════

def generate_market_insight(
    sales_summary: Dict[str, Any],
    market_summary: Dict[str, Any]
) -> InsightResponse:
    """
    Menghasilkan analisis dan rekomendasi bisnis dari ringkasan data
    (tanpa perlu upload CSV). Dipanggil oleh endpoint /insight/generate.
    """
    try:
        service = _LLMService()
        return service._generate_insight(sales_summary, market_summary)
    except Exception:
        return InsightResponse(
            summary_analysis="Pasar menunjukkan tren positif pada jam makan siang, namun kompetitor menawarkan harga lebih kompetitif.",
            key_recommendations=[
                "Buat paket bundling produk terlaris di jam makan siang.",
                "Penyesuaian margin harga 5% untuk bersaing dengan kompetitor sekitar.",
                "Tingkatkan promosi di segmen demografi dominan."
            ],
            risk_warning="Stok bahan baku berpotensi habis jika tidak diproyeksikan dengan ketat."
        )


class _LLMService:
    """Kelas internal untuk memanggil Ollama dari endpoint insight."""

    def __init__(self):
        self.endpoint = settings.LLM_ENDPOINT
        self.model = settings.LLM_MODEL_NAME

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> dict:
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return json.loads(data.get("response", "{}"))

    def _generate_insight(self, sales_summary: Dict, market_summary: Dict) -> InsightResponse:
        system_prompt = (
            "Kamu adalah AI Business Advisor senior untuk UMKM dan F&B/Retail (SiOslo). "
            "Tugasmu adalah menganalisis data penjualan dan kondisi pasar, lalu memberikan "
            "rekomendasi keputusan bisnis yang actionable, presisi, dan realistis."
        )
        user_content = f"""
        Berikut adalah data ringkasan bisnis:

        --- Sales Summary ---
        {json.dumps(sales_summary, indent=2)}

        --- Market Summary ---
        {json.dumps(market_summary, indent=2)}

        Berikan analisis singkat dan 3 rekomendasi taktis terbaik dalam format JSON dengan key:
        - "summary_analysis": string
        - "key_recommendations": list of strings
        - "risk_warning": string

        HANYA kembalikan JSON, tanpa teks lain.
        """
        result = self._call_ollama(system_prompt, user_content)
        return InsightResponse(**result)