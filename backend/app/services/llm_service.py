import os
import json
from typing import Dict, Any, Optional

# Kamu bisa menginstal library `groq` atau `together` atau menggunakan SDK pilihanmu
# Pip install contoh: pip install groq

class LLMService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        # Inisialisasi client API di sini (misal: Groq, Together, HuggingFace, dll)
        # self.client = Groq(api_key=self.api_key)

    def generate_market_insight(self, sales_summary: Dict[str, Any], market_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Menerima summary data sales dan market, lalu mengembalikan 
        insight bisnis & rekomendasi aksi berformat JSON dari Llama-3.
        """
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
        """

        # TODO: Hubungkan ke endpoint API Llama-3 milikmu
        # Contoh panggilan mock / fallback jika API Key belum terpasang:
        if not self.api_key:
            return {
                "summary_analysis": "Pasar menunjukkan tren positif pada jam makan siang, namun kompetitor menawarkan harga lebih kompetitif.",
                "key_recommendations": [
                    "Buat paket bundling produk terlaris di jam makan siang.",
                    "Penyesuaian margin harga 5% untuk bersaing dengan kompetitor sekitar.",
                    "Tingkatkan promosi di segmen demografi dominan."
                ],
                "risk_warning": "Stok bahan baku berpotensi habis jika tidak diproyeksikan dengan ketat."
            }

        # Contoh panggil API sungguhan:
        # response = self.client.chat.completions.create(
        #     model="llama3-8b-8192", # Atau model Llama-3 pilihanmu
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_content}
        #     ],
        #     response_format={"type": "json_object"}
        # )
        # return json.loads(response.choices[0].message.content)

# Global Instance
llm_service = LLMService()