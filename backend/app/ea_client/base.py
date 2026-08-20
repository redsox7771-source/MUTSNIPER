from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ListingFilter:
    min_ovr: int | None = None
    max_ovr: int | None = None
    program: str | None = None
    position: str | None = None


@dataclass(frozen=True)
class Listing:
    listing_id: str
    card_id: str
    card_name: str
    ovr: int
    program: str
    position: str
    team: str
    buy_now: int
    current_bid: int
    expires_at: datetime


class EAClient(ABC):
    """Read-only access to auction house listings. No implementation of
    this interface may perform a write request (bid, buy, list) against
    EA - search_listings is the only method for a reason."""

    @abstractmethod
    async def search_listings(self, filters: ListingFilter) -> list[Listing]: ...


class EAAuthError(Exception):
    """Raised when EA rejects the session (401) - token needs refreshing."""


class EARateLimitError(Exception):
    """Raised on 429 from EA."""


class EAServerError(Exception):
    """Raised on 5xx from EA."""
