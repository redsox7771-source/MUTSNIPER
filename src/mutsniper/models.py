from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Listing:
    """A single auction house listing, as observed on one poll."""

    auction_id: str
    card_id: str
    card_name: str
    quality: str
    ovr: int
    position: str
    team: str
    start_bid: int
    buy_now_price: int
    current_bid: int
    expiry_ts: int
    seen_ts: int


@dataclass(frozen=True)
class MarketStats:
    card_id: str
    median_price: float
    sample_count: int


@dataclass(frozen=True)
class SnipeResult:
    listing: Listing
    market_median: float
    discount_pct: float
    sample_count: int
