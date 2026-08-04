# app/services/correlation_engine.py
import pandas as pd
from typing import Dict, Any

def calculate_correlation(cleaned_df: pd.DataFrame, target_lokasi: str) -> Dict[str, Any]:
    """
    Placeholder untuk ch3coo – menghitung skor korelasi antara data penjualan
    dan data pasar lokal (demographics, foot_traffic, competitor_prices).

    Return dictionary dengan minimal:
        - keyword_overlap_score: float (0-1)
        - market_trend_growth: str (e.g. "+12%")
        - trend_reference_source: str
    """
    # Untuk development, kembalikan nilai dummy
    return {
        "keyword_overlap_score": 0.78,
        "market_trend_growth": "+22%",
        "trend_reference_source": "foot_traffic & competitor_prices"
    }