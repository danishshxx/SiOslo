from __future__ import annotations

import re
from typing import Optional

import pandas as pd

SALES_TEXT_COLUMNS = ["product_name", "category"]
SALES_PRICE_COLUMN = "unit_price"

DEMOGRAPHICS_TEXT_COLUMNS = ["category", "keywords", "segment_name"]
COMPETITOR_MATCH_COLUMNS = ["category", "product_name"]
COMPETITOR_PRICE_COLUMN = "price"

STOPWORDS = {
    "dan", "atau", "yang", "untuk", "dengan", "di", "ke", "dari", "ini", "itu",
    "the", "and", "or", "for", "with", "a", "an", "of", "in", "on",
}


def normalize_text_tokens(raw_text) -> set[str]:
    if pd.isna(raw_text):
        return set()
    text = re.sub(r"[^\w\s]", " ", str(raw_text).lower())
    return {t for t in text.split() if t} - STOPWORDS


def clean_price_value(raw_value) -> Optional[float]:
    if pd.isna(raw_value):
        return None
    s = str(raw_value).strip()
    s = re.sub(r"(?i)rp\.?\s*", "", s).replace(" ", "")
    if re.match(r"^-?\d{1,3}(\.\d{3})+(,\d+)?$", s):
        s = s.replace(".", "").replace(",", ".")
    elif re.match(r"^-?\d+,\d+$", s):
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        val = float(s)
        return val if val > 0 else None
    except ValueError:
        return None


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return round(len(a & b) / len(a | b), 4)


def compute_keyword_overlap_score(sales_df: pd.DataFrame, demographics_df: pd.DataFrame) -> dict:
    missing = [c for c in SALES_TEXT_COLUMNS if c not in sales_df.columns]
    if missing:
        return {"status": "error", "reason": f"Kolom sales_df tidak lengkap: {missing}"}

    if demographics_df is None or demographics_df.empty:
        return {"status": "no_reference_data", "reason": "Tabel demographics kosong.", "per_product": []}

    missing = [c for c in DEMOGRAPHICS_TEXT_COLUMNS if c not in demographics_df.columns]
    if missing:
        return {"status": "error", "reason": f"Kolom demographics_df tidak lengkap: {missing}"}

    demo_tokens = []
    for _, row in demographics_df.iterrows():
        tokens = normalize_text_tokens(row.get("keywords", "")) | normalize_text_tokens(row.get("segment_name", ""))
        demo_tokens.append({
            "category": str(row.get("category", "")).strip().lower(),
            "tokens": tokens,
            "segment_name": row.get("segment_name"),
        })

    results = []
    for _, prod in sales_df.iterrows():
        category = str(prod.get("category", "")).strip().lower()
        product_tokens = normalize_text_tokens(prod.get("product_name")) | normalize_text_tokens(category)
        candidates = [d for d in demo_tokens if d["category"] == category]

        if not candidates:
            results.append({
                "product_name": prod.get("product_name"), "category": prod.get("category"),
                "keyword_overlap_score": 0.0, "matched_keywords": [],
                "note": "Tidak ada demographics dengan kategori yang sama.",
            })
            continue

        best_score, best_match = 0.0, None
        for cand in candidates:
            score = _jaccard(product_tokens, cand["tokens"])
            if score > best_score:
                best_score, best_match = score, cand

        matched = sorted(product_tokens & best_match["tokens"]) if best_match else []
        results.append({
            "product_name": prod.get("product_name"), "category": prod.get("category"),
            "keyword_overlap_score": best_score, "matched_keywords": matched,
            "matched_segment": best_match["segment_name"] if best_match else None,
        })

    return {"status": "success", "per_product": results}


def compute_price_competitiveness_score(sales_df: pd.DataFrame, competitor_prices_df: pd.DataFrame) -> dict:
    if SALES_PRICE_COLUMN not in sales_df.columns:
        return {"status": "no_reference_data", "reason": f"sales_df tidak punya kolom '{SALES_PRICE_COLUMN}'.", "per_product": []}

    if competitor_prices_df is None or competitor_prices_df.empty:
        return {"status": "no_reference_data", "reason": "Tabel competitor_prices kosong.", "per_product": []}

    missing = [c for c in COMPETITOR_MATCH_COLUMNS if c not in competitor_prices_df.columns]
    if missing or COMPETITOR_PRICE_COLUMN not in competitor_prices_df.columns:
        return {"status": "error", "reason": f"Kolom competitor_prices_df tidak lengkap: {missing}"}

    results = []
    for _, prod in sales_df.iterrows():
        category = str(prod.get("category", "")).strip().lower()
        user_price = clean_price_value(prod.get(SALES_PRICE_COLUMN))

        if user_price is None:
            results.append({"product_name": prod.get("product_name"), "price_competitiveness_score": None,
                             "note": "Harga user tidak valid/kosong.", "competitor_refs": []})
            continue

        candidates = competitor_prices_df[
            competitor_prices_df["category"].astype(str).str.strip().str.lower() == category
        ]
        if candidates.empty:
            results.append({"product_name": prod.get("product_name"), "price_competitiveness_score": None,
                             "note": "Tidak ada kompetitor untuk kategori ini.", "competitor_refs": []})
            continue

        prices = [p for p in (clean_price_value(x) for x in candidates[COMPETITOR_PRICE_COLUMN]) if p is not None]
        if not prices:
            results.append({"product_name": prod.get("product_name"), "price_competitiveness_score": None,
                             "note": "Data harga kompetitor tidak valid.", "competitor_refs": []})
            continue

        avg_price = sum(prices) / len(prices)
        score = round(max(0.0, min(1.0, 0.5 + ((avg_price - user_price) / avg_price) * 0.5)), 4)

        results.append({
            "product_name": prod.get("product_name"), "price_competitiveness_score": score,
            "user_price": user_price, "avg_competitor_price": round(avg_price, 2),
            "competitor_refs": [
                {"competitor_name": r.get("competitor_name"), "price": clean_price_value(r.get(COMPETITOR_PRICE_COLUMN))}
                for _, r in candidates.iterrows()
            ],
        })

    return {"status": "success", "per_product": results}


def compute_correlation(sales_df: pd.DataFrame, demographics_df: pd.DataFrame, competitor_prices_df: pd.DataFrame) -> dict:
    if sales_df is None or sales_df.empty:
        return {"status": "error", "reason": "sales_df kosong.", "correlation_data": None}

    return {
        "status": "success",
        "correlation_data": {
            "data_source": "static_snapshot",
            "method": "jaccard_token_overlap + linear_price_comparison",
            "keyword_overlap": compute_keyword_overlap_score(sales_df, demographics_df),
            "price_competitiveness": compute_price_competitiveness_score(sales_df, competitor_prices_df),
        },
    }


if __name__ == "__main__":
    import json

    sales_df = pd.DataFrame([
        {"product_name": "Kaos Polos Pastel", "category": "Fashion", "unit_price": "65000"},
        {"product_name": "Jaket Denim Lama", "category": "Fashion", "unit_price": "180000"},
        {"product_name": "Tas Kanvas Y2K", "category": "Aksesoris", "unit_price": "90000"},
    ])
    demographics_df = pd.DataFrame([
        {"category": "Fashion", "segment_name": "Gen Z Pecinta Warna Pastel",
         "keywords": "pastel oversized kaos", "age_group": "16-24", "source": "TikTok"},
        {"category": "Aksesoris", "segment_name": "Gen Z Nostalgia Y2K",
         "keywords": "y2k tas kanvas retro", "age_group": "16-24", "source": "Instagram"},
    ])
    competitor_prices_df = pd.DataFrame([
        {"category": "Fashion", "product_name": "Kaos Pastel", "competitor_name": "TokoA", "price": "75000"},
        {"category": "Aksesoris", "product_name": "Tas Kanvas", "competitor_name": "TokoC", "price": "95000"},
    ])

    print(json.dumps(compute_correlation(sales_df, demographics_df, competitor_prices_df), indent=2, ensure_ascii=False, default=str))

# =================================================================
# WRAPPER -- dipakai app/api/v1/endpoints/analyze.py
# =================================================================

def calculate_correlation(sales_df: pd.DataFrame, target_lokasi: str, db) -> dict:
    """
    Adapter untuk endpoint /analyze/. Beda dari compute_correlation():
    - Query sendiri demographics & competitor_prices dari database (butuh db session)
    - Meratakan hasil per-produk (list) jadi satu angka representatif,
      karena analyze.py butuh satu skor tunggal untuk seluruh analisis,
      bukan skor per baris produk.

    target_lokasi TIDAK dipakai untuk filter query -- skema demographics/
    competitor_prices (ch3coo) sengaja tidak punya kolom lokasi (fokus MVP
    saat ini: Dead-Stock Pivot via keyword matching, bukan Hyper-Local).
    target_lokasi cuma diteruskan sebagai teks konteks ke LLM di langkah
    berikutnya (generate_innovation_blueprint), bukan dipakai di sini.
    """
    from app.models.market import Demographic, CompetitorPrice

    demo_rows = db.query(Demographic).all()
    demographics_df = pd.DataFrame([{
        "category": d.category,
        "segment_name": d.segment_name,
        "keywords": d.keywords,
        "age_group": d.age_group,
        "source": d.source,
    } for d in demo_rows])

    comp_rows = db.query(CompetitorPrice).all()
    competitor_prices_df = pd.DataFrame([{
        "category": c.category,
        "product_name": c.product_name,
        "competitor_name": c.competitor_name,
        "price": c.price,
    } for c in comp_rows])

    result = compute_correlation(sales_df, demographics_df, competitor_prices_df)
    corr_data = result.get("correlation_data") or {}

    keyword_overlap = corr_data.get("keyword_overlap", {})
    per_product = keyword_overlap.get("per_product", [])
    if per_product:
        avg_score = sum(p["keyword_overlap_score"] for p in per_product) / len(per_product)
        best = max(per_product, key=lambda p: p["keyword_overlap_score"])
        trend_source = best.get("matched_segment") or "N/A"
    else:
        avg_score = 0.0
        trend_source = keyword_overlap.get("reason", "Belum ada data tren referensi.")

    return {
        "keyword_overlap_score": round(avg_score, 4),
        "market_trend_growth": "+0%",  # TODO: belum ada logika hitung growth dari data historis
        "trend_reference_source": trend_source,
        "raw_correlation_data": corr_data,  # detail lengkap per-produk, untuk confidence trail nanti
    }
