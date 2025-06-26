from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

class Settings(BaseSettings):
    secret_key: str = Field(..., alias="SECRET_KEY")
    db_host: str = Field("localhost", env="POSTGRES_HOST")
    db_port: int = Field(5432, env="POSTGRES_PORT")
    db_user: str = Field("admin", env="POSTGRES_USER")
    db_password: str = Field("123456", env="POSTGRES_PASS")
    db_name: str = Field("postgres", env="POSTGRES_DB")

    model_config = SettingsConfigDict(
        env_file=env_path,  
        extra="ignore",
        case_sensitive=False
    )
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

@lru_cache
def get_settings() -> Settings:
    return Settings()
