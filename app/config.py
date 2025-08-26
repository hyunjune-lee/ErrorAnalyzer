import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./error_analyzer.db"
    
    # NELO API Configuration
    nelo_access_key: str = os.getenv("NELO_ACCESS_KEY", "")
    nelo_secret_key: str = os.getenv("NELO_SECRET_KEY", "")
    nelo_api_url: str = os.getenv("NELO_API_URL", "https://nelo.navercorp.com/api/v2/download/logs")
    nelo_group_id: str = os.getenv("NELO_GROUP_ID", "6370")
    
    # AI API Configuration
    ai_api_url: str = os.getenv("AI_API_URL", "")
    ai_api_key: str = os.getenv("AI_API_KEY", "")
    
    # Log Source Configuration
    log_source_type: str = os.getenv("LOG_SOURCE_TYPE", "file")  # "nelo" or "file"
    log_source_path: str = os.getenv("LOG_SOURCE_PATH", "sample_logs.json")
    pipeline_interval_seconds: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()