from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "SiOslo: Market-Driven R&D Buddy"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    DATABASE_URL: str
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None  # Typo 'SUPANBASE' udah diperbaiki
    
    LLM_ENDPOINT: str = "http://host.docker.internal:11434/api/generate"
    LLM_MODEL_NAME: str = "llama3:8b-instruct"
    
    # Standar Pydantic v2 untuk membaca file .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Mencegah error kalau di .env ada variabel ekstra yang nggak masuk ke class ini
    )
        
@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()