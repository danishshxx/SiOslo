from fastapi import APIRouter
from app.api.v1.endpoints import sales, market, insight, analyze

api_router = APIRouter()


api_router.include_router(sales.router)
api_router.include_router(market.router)
api_router.include_router(insight.router)
api_router.include_router(analyze.router)