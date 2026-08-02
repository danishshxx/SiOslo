from fastapi import APIRouter
from app.api.v1.endpoints import sales, market

api_router = APIRouter()

# Daftarin router dari masing-masing module
api_router.include_router(sales.router)
api_router.include_router(market.router) # <--- Ini yang tadinya v1_router diganti jadi api_router