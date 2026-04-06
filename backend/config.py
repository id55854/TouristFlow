"""Application configuration from environment."""

from datetime import date
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_iso_date(s: str | None) -> Optional[date]:
    if not s or not str(s).strip():
        return None
    parts = str(s).strip().split("-")
    if len(parts) != 3:
        return None
    y, m, d = (int(parts[0]), int(parts[1]), int(parts[2]))
    return date(y, m, d)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./touristflow.db"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    touristflow_demo_date: str | None = None
    touristflow_managed_host: str | None = None

    @property
    def demo_today(self) -> Optional[date]:
        return _parse_iso_date(self.touristflow_demo_date)

    @property
    def sqlite_path(self) -> Path | None:
        if self.database_url.startswith("sqlite:///"):
            path = self.database_url.replace("sqlite:///", "", 1)
            if path.startswith("./"):
                return Path(__file__).resolve().parent / path[2:]
            if not path.startswith(":"):
                return Path(path).resolve()
        return None


settings = Settings()
