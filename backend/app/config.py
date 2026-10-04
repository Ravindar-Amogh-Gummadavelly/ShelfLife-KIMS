from pathlib import Path
from typing import Self

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: SecretStr
    mongodb_database: str

    @field_validator("mongodb_uri", mode="before")
    @classmethod
    def strip_mongodb_uri(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("mongodb_database", mode="before")
    @classmethod
    def strip_database_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_nonempty_values(self) -> Self:
        if not self.mongodb_uri.get_secret_value():
            raise ValueError("MONGODB_URI must not be empty")
        if not self.mongodb_database:
            raise ValueError("MONGODB_DATABASE must not be empty")
        return self


def get_settings() -> Settings:
    return Settings()
