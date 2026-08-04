# File: app/schemas/analysis.py
from pydantic import BaseModel, Field
from typing import List, Optional

class DataHealthMetric(BaseModel):
    reliability_score: int = Field(..., ge=0, le=100)
    status_color: str = Field(..., example="green")  # green, yellow, red
    warning_message: Optional[str] = None

class CorrelationMetric(BaseModel):
    keyword_overlap_score: float = Field(..., ge=0.0, le=1.0)
    market_trend_growth: str = Field(..., example="+65%")
    trend_reference_source: str

class InnovationBlueprintItem(BaseModel):
    id: str = Field(..., example="inv-001")
    title: str
    target_location: str
    recommended_price: int
    competitor_price_ceiling: int
    justification: str
    risk_factors: List[str]
    whatsapp_copy_text: str = Field(..., description="Teks promosi siap salin untuk WA Business")

class AnalysisResponse(BaseModel):
    status: str = Field(..., example="success")
    data_health: DataHealthMetric
    correlation_metrics: CorrelationMetric
    innovation_blueprint: List[InnovationBlueprintItem]