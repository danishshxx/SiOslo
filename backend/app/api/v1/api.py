from fastapi import APIRouter
from app.api.v1.endpoints import sales, market, insight, analyze, simulate, chat

api_router = APIRouter()

api_router.include_router(sales.router)
api_router.include_router(market.router)
api_router.include_router(insight.router)
api_router.include_router(analyze.router)
api_router.include_router(simulate.router)
api_router.include_router(chat.router)