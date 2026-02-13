from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_STORAGE_CONTAINER_NAME: str
    STORAGE_ROOT: str
    WORKSPACE_ROOT: str
    MONGO_API_URL: str | None = Field(default=None, alias="MONGO_API_URL")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()