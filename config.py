from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

class Settings(BaseSettings):
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    user_db_name: str = "users"

    class Config:
        env_prefix = ""
        env_file = Path(__file__).parent / ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
