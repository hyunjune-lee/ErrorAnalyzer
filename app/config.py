import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./error_analyzer.db"
    ai_api_url: str = os.getenv("AI_API_URL", "")
    ai_api_key: str = os.getenv("AI_API_KEY", "")
    log_source_path: str = os.getenv("LOG_SOURCE_PATH", "sample_logs.json")
    pipeline_interval_seconds: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()