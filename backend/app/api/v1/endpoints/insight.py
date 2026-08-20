from fastapi import APIRouter, HTTPException, status
from app.schemas.insight import InsightRequest, InsightResponse
from app.services.llm_service import generate_market_insight   # import fungsi, bukan instance

router = APIRouter(prefix="/insight", tags=["AI Insight"])

@router.post("/generate", response_model=InsightResponse, status_code=status.HTTP_200_OK)
def generate_ai_insight(payload: InsightRequest):
    try:
        result = generate_market_insight(
            sales_summary=payload.sales_summary,
            market_summary=payload.market_summary
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memproses rekomendasi AI: {str(e)}"
        )