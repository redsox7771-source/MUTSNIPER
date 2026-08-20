from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MUTSNIPER_", extra="ignore")

    database_url: str = "postgresql+asyncpg://mutsniper:mutsniper@localhost:5432/mutsniper"

    ea_client: str = "mock"  # "mock" | "real"
    ea_endpoint_url: str = ""
    ea_http_method: str = "GET"
    ea_token: str = ""
    ea_headers_json: str = "{}"
    ea_request_template_json: str = "{}"

    watchlist_json: str = "[]"

    poll_interval_min_seconds: float = 4.0
    poll_interval_max_seconds: float = 8.0
    poll_rate_cap_per_minute: int = 20

    price_window_hours: int = 6
    price_min_samples: int = 8
    ah_tax_rate: float = 0.10
    snipe_margin_threshold: float = 0.25

    discord_alerts_enabled: bool = False
    discord_webhook_url: str = ""


settings = Settings()
