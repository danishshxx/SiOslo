from fastapi import APIRouter
from app.api.v1.endpoints import sales, market, insight

api_router = APIRouter()

# Daftarin router dari masing-masing module
api_router.include_router(sales.router)
api_router.include_router(market.router)
api_router.include_router(insight.router) 