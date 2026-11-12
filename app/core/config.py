from functools import lru_cache
from pydantic_settings import SettingsConfigDict, BaseSettings
from sqlalchemy.engine import URL


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    OPENAI_API_KEY: str
    OPENAI_MODEL: str

    REDIS_URL: str

    @property
    def database_url(self) -> URL:
        url = URL.create(
            drivername="postgresql+asyncpg",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME
        )
        return url


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
