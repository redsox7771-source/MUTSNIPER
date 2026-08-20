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


class OwnedCardOut(BaseModel):
    card_id: str
    card_name: str
    ovr: int
    program: str
    position: str
    team: str
    quantity: int
    tradeable: bool


class BuyResult(BaseModel):
    listing_id: str
    success: bool
    price_paid: int
    message: str


class ListCardRequest(BaseModel):
    buy_now_price: int
    start_bid: int
    duration_seconds: int = 3600


class ListCardResult(BaseModel):
    card_id: str
    success: bool
    listing_id: str | None
    message: str


class PurchaseOut(BaseModel):
    listing_id: str
    card_id: str
    price_paid: int
    success: bool
    message: str
    purchased_at: datetime


class RecentSaleOut(BaseModel):
    listing_id: str
    price: int
    sold_at: datetime


class ActiveListingOut(BaseModel):
    listing_id: str
    buy_now: int
    current_bid: int
    expires_at: datetime


class CardMarketOut(BaseModel):
    recent_sales: list[RecentSaleOut]
    active_listings: list[ActiveListingOut]
