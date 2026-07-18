from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "StudyWise AI"
    jwt_secret: str = Field(default="change-this-in-development", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")
    ai_provider: str = Field(default="gemini", alias="AI_PROVIDER")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-20b", alias="GROQ_MODEL")
    ai_fallback_provider: str | None = Field(default="groq", alias="AI_FALLBACK_PROVIDER")
    ai_timeout_seconds: int = Field(default=45, alias="AI_TIMEOUT_SECONDS")
    chroma_enabled: bool = Field(default=True, alias="CHROMA_ENABLED")
    chroma_dir: str = Field(default="./data/chroma", alias="CHROMA_DIR")
    chroma_collection: str = Field(default="studywise_chunks", alias="CHROMA_COLLECTION")

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def chroma_path(self) -> Path:
        path = Path(self.chroma_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
