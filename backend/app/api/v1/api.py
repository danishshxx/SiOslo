from fastapi import APIRouter
from app.api.v1.endpoints import sales
# Nanti kalau ada endpoint lain (misal analyze.py), tinggal import dan tambahin di sini

api_router = APIRouter()

# Kita gabungin router sales ke dalam agregator v1
api_router.include_router(sales.router)