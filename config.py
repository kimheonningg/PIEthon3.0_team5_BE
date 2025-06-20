from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

class Settings(BaseSettings):
    secret_key: str = Field(..., alias="SECRET_KEY")
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    admin_db_name: str = "admin"

    model_config = SettingsConfigDict(
        env_file=env_path,  
        extra="ignore",
        case_sensitive=False
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
