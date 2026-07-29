from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "SiOslo: Market-Driven R&D Buddy"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    DATABASE_URL: str
    SUPABASE_URL: str | None = None
    SUPANBASE_KEY: str | None = None
    
    LLM_ENDPOINT: str = "http://host.docker.internal:11434/api/generate"
    LLM_MODEL_NAME: str = "llama3:8b-instruct"
    
    class config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()