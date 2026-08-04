import os
import json
import requests
from typing import Dict, Any, Optional, List
from app.schemas.insight import InsightResponse
from app.core.config import settings
import pandas as pd
from app.schemas.analysis import InnovationBlueprintItem

# ------------------------------------------------------------------
# Fungsi yang langsung dipanggil oleh endpoint insight
# ------------------------------------------------------------------
def generate_market_insight(
    sales_summary: Dict[str, Any],
    market_summary: Dict[str, Any]
) -> InsightResponse:
    """
    Memanggil LLM lokal (Ollama) untuk menghasilkan insight dari ringkasan data.
    Jika LLM tidak tersedia, mengembalikan mock response.
    """
    service = LLMService()
    return service._generate(sales_summary, market_summary)


# ------------------------------------------------------------------
# Kelas utama LLM Service (dapat digunakan juga oleh endpoint lain)
# ------------------------------------------------------------------
class LLMService:
    def __init__(self):
        self.llm_endpoint = settings.LLM_ENDPOINT  # e.g. http://localhost:11434/api/generate
        self.model_name = settings.LLM_MODEL_NAME       # e.g. llama3:8b

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> dict:
        """Panggil Ollama API, kembalikan dict hasil parsing JSON."""
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        try:
            resp = requests.post(
                self.llm_endpoint,
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "format": "json"   # minta output JSON langsung
                },
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            # Ollama menyimpan output di field "response"
            llm_output = data.get("response", "{}")
            return json.loads(llm_output)
        except Exception:
            # Jika LLM tidak tersedia, lempar exception atau kembalikan mock
            raise RuntimeError("LLM service tidak dapat dihubungi")

    def _generate(
        self,
        sales_summary: Dict[str, Any],
        market_summary: Dict[str, Any]
    ) -> InsightResponse:
        system_prompt = (
            "Kamu adalah AI Business Advisor senior untuk UMKM dan F&B/Retail (SiOslo). "
            "Tugasmu adalah menganalisis data penjualan dan kondisi pasar, lalu memberikan "
            "rekomendasi keputusan bisnis yang actionable, presisi, dan realistis."
        )

        user_content = f"""
        Berikut adalah data ringkasan bisnis:

        --- Sales Summary ---
        {json.dumps(sales_summary, indent=2)}

        --- Market Summary ---
        {json.dumps(market_summary, indent=2)}

        Berikan analisis singkat dan 3 rekomendasi taktis terbaik dalam format JSON dengan key:
        - "summary_analysis": string
        - "key_recommendations": list of strings
        - "risk_warning": string

        HANYA kembalikan JSON, tanpa teks lain.
        """

        # Coba panggil Ollama, jika gagal fallback ke mock
        try:
            result = self._call_ollama(system_prompt, user_content)
            # Validasi dan kembalikan sebagai InsightResponse
            return InsightResponse(**result)
        except Exception:
            # Fallback mock untuk development
            return InsightResponse(
                summary_analysis="Pasar menunjukkan tren positif pada jam makan siang, namun kompetitor menawarkan harga lebih kompetitif.",
                key_recommendations=[
                    "Buat paket bundling produk terlaris di jam makan siang.",
                    "Penyesuaian margin harga 5% untuk bersaing dengan kompetitor sekitar.",
                    "Tingkatkan promosi di segmen demografi dominan."
                ],
                risk_warning="Stok bahan baku berpotensi habis jika tidak diproyeksikan dengan ketat."
            )
    
def generate_innovation_blueprint(
    cleaned_data: pd.DataFrame,
    data_health: Dict,
    correlation_metrics: Dict,
    target_lokasi: str
) -> List[InnovationBlueprintItem]:
    """
    Placeholder untuk LLM – menghasilkan blueprint inovasi.
    Nanti akan membangun prompt dan memanggil Ollama.
    """
    # Dummy response
    return [
        InnovationBlueprintItem(
            id="inv-001",
            title="Paket Hemat Makan Siang",
            target_location=target_lokasi,
            recommended_price=20000,
            competitor_price_ceiling=25000,
            justification="Berdasarkan foot traffic tinggi di jam makan siang dan harga kompetitor.",
            risk_factors=["Fluktuasi harga bahan"],
            whatsapp_copy_text="Yuk coba Paket Hemat Makan Siang kami! 🍱"
        )
    ]