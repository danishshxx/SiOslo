from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter(prefix="/chat", tags=["AI Mentor Chat"])

# --- SCHEMAS ---
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# --- LOGIC ---
@router.post("/", response_model=ChatResponse)
async def ai_mentor_chat(req: ChatRequest):
    """
    Endpoint interaktif untuk ngobrol dengan AI Mentor SiOslo.
    """
    # Mengambil endpoint dan nama model dari .env (atau hardcode ke nilai Docker)
    llm_endpoint = os.getenv("LLM_ENDPOINT", "http://ollama:11434/api/generate")
    llm_model = os.getenv("LLM_MODEL_NAME", "sioslo")

    # System prompt agar AI menjawab layaknya mentor bisnis
    system_prompt = (
        "Kamu adalah SiOslo Buddy, mentor bisnis AI yang ramah, profesional, "
        "dan ahli dalam strategi UMKM. Jawab pertanyaan dengan singkat, padat, "
        "dan berikan insight yang aplikatif."
    )
    
    full_prompt = f"{system_prompt}\n\nUser: {req.message}\nSiOslo Buddy:"

    payload = {
        "model": llm_model,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        # Panggil Ollama secara asinkron agar tidak memblokir FastAPI
        async with httpx.AsyncClient() as client:
            response = await client.post(llm_endpoint, json=payload, timeout=120.0)
            response.raise_for_status()
            
            data = response.json()
            return ChatResponse(reply=data.get("response", "Maaf, mentor sedang tidak fokus."))
            
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="AI Mentor terlalu lama berpikir (Timeout).")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Gagal menghubungi AI Mentor: {str(e)}")