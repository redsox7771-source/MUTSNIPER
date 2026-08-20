from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SnipeOut(BaseModel):
    listing_id: str
    card_id: str
    card_name: str
    ovr: int
    program: str
    position: str
    buy_now: int
    est_value: float
    margin: float
    margin_pct: float
    expires_at: datetime
    detected_at: datetime


class PriceHistoryPoint(BaseModel):
    price: int
    observed_at: datetime
    source: str
