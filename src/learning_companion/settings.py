from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Values come from the environment or an untracked .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    groq_api_key: SecretStr = SecretStr("")
    groq_api_base_url: str = "https://api.groq.com"
    groq_model_name: str = ""
    host: str = "127.0.0.1"
    port: int = 8000

    def missing_setting(self) -> str | None:
        """Name the first setting a model call needs but does not have."""
        if not self.groq_api_key.get_secret_value().strip():
            return "GROQ_API_KEY"
        if not self.groq_model_name.strip():
            return "GROQ_MODEL_NAME"
        return None


@lru_cache
def get_settings() -> Settings:
    """Read settings once at startup. Editing .env means restarting the app."""
    return Settings()
