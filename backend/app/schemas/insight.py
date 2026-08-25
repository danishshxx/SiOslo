from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any

class InsightRequest(BaseModel):
    sales_summary: Dict[str, Any] = Field(
        default_factory=dict,
        json_schema_extra={
            "example": {
                "total_sales_idr": 15000000,
                "top_product": "Kopi Susu Aren",
                "total_transactions": 320
            }
        }
    )
    market_summary: Dict[str, Any] = Field(
        default_factory=dict,
        json_schema_extra={
            "example": {
                "peak_foot_traffic": "12:00 - 14:00",
                "competitor_avg_price": 22000,
                "target_demographic": "Mahasiswa / Workers 18-25"
            }
        }
    )

class InsightResponse(BaseModel):
    summary_analysis: str
    key_recommendations: List[str]
    risk_warning: str

    model_config = ConfigDict(from_attributes=True)