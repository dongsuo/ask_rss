"""
Example configuration for the RSS Feed Processor API.

Copy this file to `config.py` and update the values as needed.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, AnyHttpUrl, validator

class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RSS Feed Processor API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    WORKERS: int = 1
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Hugging Face settings
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
    HF_MODEL_NAME: str = "sentence-transformers/all-mpnet-base-v2"
    
    # Dataset settings
    DEFAULT_BATCH_SIZE: int = 32
    DEFAULT_MAX_ARTICLES: int = 100
    DATASET_CACHE_DIR: str = "datasets"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = "logs/app.log"
    
    # Cache settings (in seconds)
    CACHE_TTL: int = 3600  # 1 hour
    
    # Rate limiting
    RATE_LIMIT: str = "1000/day, 100/hour"
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings()

# Example usage:
if __name__ == "__main__":
    print(f"{settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"Server: {settings.HOST}:{settings.PORT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
