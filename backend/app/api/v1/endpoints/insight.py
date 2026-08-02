from fastapi import APIRouter, HTTPException, status
from app.schemas.insight import InsightRequest, InsightResponse
from app.services.llm_service import llm_service

router = APIRouter(prefix="/insight", tags=["AI Insight"])

@router.post("/generate", response_model=InsightResponse, status_code=status.HTTP_200_OK)
def generate_ai_insight(payload: InsightRequest):
    """
    Menerima ringkasan data sales & market, lalu memprosesnya
    menggunakan Llama-3 (llm_service) untuk menghasilkan analisis dan strategi bisnis.
    """
    try:
        result = llm_service.generate_market_insight(
            sales_summary=payload.sales_summary,
            market_summary=payload.market_summary
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memproses rekomendasi AI: {str(e)}"
        )