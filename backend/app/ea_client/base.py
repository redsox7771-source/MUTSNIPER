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


@dataclass(frozen=True)
class OwnedCard:
    card_id: str
    card_name: str
    ovr: int
    program: str
    position: str
    team: str
    quantity: int
    tradeable: bool


@dataclass(frozen=True)
class PurchaseResult:
    listing_id: str
    success: bool
    price_paid: int
    message: str


@dataclass(frozen=True)
class ListResult:
    card_id: str
    success: bool
    listing_id: str | None
    message: str


class EAClient(ABC):
    """Auction house access for a single EA account.

    search_listings and get_binder are read-only. buy_now and list_card
    execute real purchases/listings against EA - these exist only for the
    account owner's own explicit, human-triggered actions. They must
    never be called autonomously (no auto-buying the moment a snipe is
    detected) and must never be wired up for a pooled/linked friend's
    account without that person separately and explicitly consenting to
    write access, distinct from read-only pool participation.
    """

    @abstractmethod
    async def search_listings(self, filters: ListingFilter) -> list[Listing]: ...

    @abstractmethod
    async def get_binder(self) -> list[OwnedCard]: ...

    @abstractmethod
    async def buy_now(self, listing_id: str) -> PurchaseResult: ...

    @abstractmethod
    async def list_card(
        self, card_id: str, buy_now_price: int, start_bid: int, duration_seconds: int
    ) -> ListResult: ...


class EAAuthError(Exception):
    """Raised when EA rejects the session (401) - token needs refreshing."""


class EARateLimitError(Exception):
    """Raised on 429 from EA."""


class EAServerError(Exception):
    """Raised on 5xx from EA."""
