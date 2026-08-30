from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    db_name: str
    db_user: str
    db_password: str
    db_port: int
    db_host: str
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "apartment-api"
    jwt_audience: str = "apartment-web"
    access_token_expire_seconds: int = 900

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache
def get_settings() -> Settings:
    """Создаёт настройки только в момент, когда они действительно нужны."""
    return Settings()


class CorsSettings(BaseSettings):
    """Настройки CORS, не зависящие от параметров подключения к БД."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    cors_allowed_origins: str = "http://localhost:5173"


@lru_cache
def get_cors_allowed_origins() -> list[str]:
    """Возвращает разрешённые origin из разделённой запятыми переменной окружения."""
    settings = CorsSettings()
    return [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
