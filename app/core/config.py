from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    mongo_api_url: str | None = Field(default=None, alias="MONGO_API_URL")
    STORAGE_ROOT: str
    WORKSPACE_ROOT: str   # 👈 ADD THIS

    class Config:
        env_file = ".env"
        extra="ignore"   # 🔥 THIS FIXES YOUR ERROR

settings = Settings()



