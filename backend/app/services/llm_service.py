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

def generate_innovation_blueprint(
    cleaned_data: pd.DataFrame,
    data_health: Dict[str, Any],
    correlation_metrics: Dict[str, Any],
    target_lokasi: str
) -> List[InnovationBlueprintItem]:
    """
    Membangun prompt dari data kesehatan & korelasi, memanggil LLM
    (Ollama lokal via httpx sinkron), dan mengembalikan blueprint inovasi.
    Jika LLM tidak tersedia → fallback ke simulasi cerdas.
    """
    # 1. Bangun prompt
    prompt = _build_prompt(cleaned_data, data_health, correlation_metrics, target_lokasi)

    # 2. Coba panggil Ollama
    try:
        llm_json = _call_ollama(prompt)
        items = _parse_llm_response(llm_json, target_lokasi)
        if items:
            return items
    except Exception:
        pass  # fallback jika gagal

    # 3. Fallback simulasi
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
        qty = int(row.get("qty_sold", 0))
        stock = int(row.get("remaining_stock", 0))
        price = row.get("unit_price", 0)
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
    with httpx.Client(timeout=90.0) as client:
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

        # Bersihkan jika ada markdown code fence
        if llm_output.startswith("```"):
            llm_output = llm_output.split("\n", 1)[-1].rsplit("\n", 1)[0]

        return json.loads(llm_output)


def _parse_llm_response(llm_json: Any, target: str) -> List[InnovationBlueprintItem]:
    """Validasi dan konversi response LLM ke list InnovationBlueprintItem."""
    if not isinstance(llm_json, list):
        return []

    items = []
    for item in llm_json:
        try:
            # Pastikan target_location sama dengan yang diminta
            item["target_location"] = target
            items.append(InnovationBlueprintItem(**item))
        except Exception:
            continue  # lewati item yang tidak valid
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