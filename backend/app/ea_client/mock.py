from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

from .base import EAClient, Listing, ListingFilter

# (card_id, name, ovr, program, position, team)
_CARD_POOL = [
    ("101", "Justin Jefferson", 99, "Team of the Year", "WR", "Vikings"),
    ("102", "Micah Parsons", 97, "Core", "EDGE", "Cowboys"),
    ("103", "Patrick Mahomes", 98, "Fantasy", "QB", "Chiefs"),
    ("104", "Myles Garrett", 96, "Core", "EDGE", "Browns"),
    ("105", "CeeDee Lamb", 95, "Core", "WR", "Cowboys"),
    ("106", "Sauce Gardner", 94, "Core", "CB", "Jets"),
    ("107", "Nick Bosa", 96, "Core", "EDGE", "49ers"),
    ("108", "Tyreek Hill", 97, "Fantasy", "WR", "Dolphins"),
]


class MockEAClient(EAClient):
    """Generates realistic fake listings so the rest of the pipeline can
    be built and exercised before a real endpoint is wired up. Never
    touches the network."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._market_price: dict[str, int] = {
            card_id: self._rng.randint(20_000, 900_000) for card_id, *_ in _CARD_POOL
        }
        self._active: dict[str, Listing] = {}

    async def search_listings(self, filters: ListingFilter) -> list[Listing]:
        self._churn()
        return [listing for listing in self._active.values() if self._matches(listing, filters)]

    @staticmethod
    def _matches(listing: Listing, filters: ListingFilter) -> bool:
        if filters.min_ovr is not None and listing.ovr < filters.min_ovr:
            return False
        if filters.max_ovr is not None and listing.ovr > filters.max_ovr:
            return False
        if filters.program and listing.program != filters.program:
            return False
        if filters.position and listing.position != filters.position:
            return False
        return True

    def _churn(self) -> None:
        now = datetime.now(timezone.utc)

        for listing_id in list(self._active):
            if self._active[listing_id].expires_at <= now:
                del self._active[listing_id]

        for _ in range(self._rng.randint(0, 3)):
            card_id, name, ovr, program, position, team = self._rng.choice(_CARD_POOL)
            market = self._market_price[card_id]

            # ~12% of new listings are an obvious snipe well under market,
            # so the pipeline has something real to detect during dev.
            if self._rng.random() < 0.12:
                price = int(market * self._rng.uniform(0.4, 0.65))
            else:
                price = int(market * self._rng.uniform(0.85, 1.15))

            listing_id = str(uuid.uuid4())
            self._active[listing_id] = Listing(
                listing_id=listing_id,
                card_id=card_id,
                card_name=name,
                ovr=ovr,
                program=program,
                position=position,
                team=team,
                buy_now=price,
                current_bid=int(price * self._rng.uniform(0.5, 0.9)),
                expires_at=now + timedelta(seconds=self._rng.randint(60, 900)),
            )
            self._market_price[card_id] = int(market * self._rng.uniform(0.98, 1.02))
