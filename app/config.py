import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./dev.db", env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    JWT_SECRET_KEY: str = Field(default="dev_secret_key_change_in_production_32chars", env="JWT_SECRET_KEY")
    EMBEDDING_DIMENSION: int = Field(default=768, env="EMBEDDING_DIMENSION")
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8501"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
