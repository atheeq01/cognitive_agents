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

    # Google / Firebase
    FIRESTORE_EMULATOR_HOST: str | None = None
    FIREBASE_PROJECT_ID: str | None = None
    PUBSUB_EMULATOR_HOST: str | None = None
    GCS_BUCKET_NAME: str = "omnimind-documents"

    # Gemini Models
    GEMINI_TEXT_MODEL: str
    GEMINI_CHAT_MODEL: str
    GEMINI_EMBEDDING_MODEL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()

import os
if settings.PUBSUB_EMULATOR_HOST:
    os.environ["PUBSUB_EMULATOR_HOST"] = settings.PUBSUB_EMULATOR_HOST
if settings.FIRESTORE_EMULATOR_HOST:
    os.environ["FIRESTORE_EMULATOR_HOST"] = settings.FIRESTORE_EMULATOR_HOST
