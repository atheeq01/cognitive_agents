from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    # Application Settings
    ENVIRONMENT: str = "local"
    DEBUG: bool = True
    PROJECT_NAME: str = "OmniMind v2 API"
    API_V1_STR: str = "/api/v1"

    # Database connections
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "local"

    # Google / Firebase
    FIRESTORE_EMULATOR_HOST: str | None = None
    FIREBASE_PROJECT_ID: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
