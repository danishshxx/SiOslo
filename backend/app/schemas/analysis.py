from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ---------------- Skema tambahan untuk detail issue ----------------
class DataHealthIssue(BaseModel):
    row_index: Optional[int] = None
    column: Optional[str] = None
    issue_type: str
    detail: str

# ---------------- Metric Kesehatan Data ----------------
class DataHealthMetric(BaseModel):
    reliability_score: int = Field(..., ge=0, le=100)
    status_color: str = Field(..., example="green")  # green, yellow, red
    warning_message: Optional[str] = None
    # Dua field baru di bawah ini:
    score_breakdown: Optional[Dict[str, Any]] = None
    issues: Optional[List[DataHealthIssue]] = None

# ---------------- Metric Korelasi (dari ch3coo) ----------------
class CorrelationMetric(BaseModel):
    keyword_overlap_score: float = Field(..., ge=0.0, le=1.0)
    market_trend_growth: str = Field(..., example="+65%")
    trend_reference_source: str

# ---------------- Blueprint Inovasi (dari LLM) ----------------
class InnovationBlueprintItem(BaseModel):
    id: str = Field(..., example="inv-001")
    title: str
    target_location: str
    recommended_price: int
    competitor_price_ceiling: int
    justification: str
    risk_factors: List[str]
    whatsapp_copy_text: str = Field(..., description="Teks promosi siap salin untuk WA Business")

# ---------------- Respons Utama ----------------
class AnalysisResponse(BaseModel):
    status: str = Field(..., example="success")
    data_health: DataHealthMetric
    correlation_metrics: CorrelationMetric
    innovation_blueprint: List[InnovationBlueprintItem]
    
class PerProductScore(BaseModel):
    product_name: str
    category: Optional[str] = None
    keyword_overlap_score: float
    matched_keywords: List[str] = []
    matched_segment: Optional[str] = None
    price_competitiveness_score: Optional[float] = None
    user_price: Optional[float] = None
    avg_competitor_price: Optional[float] = None

class CorrelationMetric(BaseModel):
    keyword_overlap_score: float = Field(..., description="Rata-rata keyword overlap semua produk")
    market_trend_growth: str = Field(..., example="+65%")
    trend_reference_source: str
    # Opsional: detail per produk
    per_product_details: Optional[List[PerProductScore]] = None