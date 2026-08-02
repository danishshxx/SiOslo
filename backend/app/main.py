from fastapi import FastAPI
from app.api.v1.api import api_router # <--- Import agregator v1 yang baru

app = FastAPI(title="SiOslo API")

# Daftarin semua rute v1 dengan prefix /api/v1
app.include_router(api_router, prefix="/api/v1") 

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to SiOslo API! Navigate to /docs for the API documentation."}