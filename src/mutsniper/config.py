from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    return default if val is None else val.strip().lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Config:
    session_path: str = os.environ.get("MUTSNIPER_SESSION_PATH", "session.json")
    db_path: str = os.environ.get("MUTSNIPER_DB_PATH", "mutsniper.db")
    watchlist: list[str] = field(
        default_factory=lambda: [
            name.strip()
            for name in os.environ.get("MUTSNIPER_WATCHLIST", "").split(",")
            if name.strip()
        ]
    )
    poll_interval_seconds: int = int(os.environ.get("MUTSNIPER_POLL_INTERVAL_SECONDS", "45"))
    snipe_threshold_pct: float = float(os.environ.get("MUTSNIPER_SNIPE_THRESHOLD_PCT", "0.30"))
    min_samples: int = int(os.environ.get("MUTSNIPER_MIN_SAMPLES", "3"))
    lookback_hours: int = int(os.environ.get("MUTSNIPER_LOOKBACK_HOURS", "72"))
    discord_webhook_url: str = os.environ.get("MUTSNIPER_DISCORD_WEBHOOK_URL", "")


CONFIG = Config()
