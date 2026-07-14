"""Application configuration from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = parent of backend/
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent

# Load root .env then backend .env (root wins for Docker/local conventions)
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(_BACKEND_DIR / ".env")


def _default_db_path() -> Path:
    env = os.environ.get("DB_PATH", "").strip()
    if env:
        return Path(env)
    # Prefer project-root db/ for volume mount compatibility
    return _PROJECT_ROOT / "db" / "finally.db"


class Settings:
    """Runtime settings for FinAlly."""

    db_path: Path = _default_db_path()
    openrouter_api_key: str = os.environ.get("OPENROUTER_API_KEY", "").strip()
    massive_api_key: str = os.environ.get("MASSIVE_API_KEY", "").strip()
    llm_mock: bool = os.environ.get("LLM_MOCK", "false").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    user_id: str = "default"
    default_cash: float = 10_000.0
    default_tickers: list[str] = [
        "AAPL",
        "GOOGL",
        "MSFT",
        "AMZN",
        "TSLA",
        "NVDA",
        "META",
        "JPM",
        "V",
        "NFLX",
    ]
    snapshot_interval_seconds: float = 30.0
    static_dir: Path = Path(
        os.environ.get("STATIC_DIR", str(_BACKEND_DIR / "static"))
    )
    cors_origins: list[str] = [
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(
            ","
        )
        if o.strip()
    ]


settings = Settings()
