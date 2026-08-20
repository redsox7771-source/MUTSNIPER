from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

from .base import EAClient, Listing, ListingFilter, ListResult, OwnedCard, PurchaseResult

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
        self._binder: dict[str, int] = {"101": 1, "105": 2}  # card_id -> quantity owned

    async def search_listings(self, filters: ListingFilter) -> list[Listing]:
        self._churn()
        return [listing for listing in self._active.values() if self._matches(listing, filters)]

    async def get_binder(self) -> list[OwnedCard]:
        cards_by_id = {card_id: (name, ovr, program, position, team) for card_id, name, ovr, program, position, team in _CARD_POOL}
        return [
            OwnedCard(
                card_id=card_id,
                card_name=cards_by_id[card_id][0],
                ovr=cards_by_id[card_id][1],
                program=cards_by_id[card_id][2],
                position=cards_by_id[card_id][3],
                team=cards_by_id[card_id][4],
                quantity=quantity,
                tradeable=True,
            )
            for card_id, quantity in self._binder.items()
            if quantity > 0
        ]

    async def buy_now(self, listing_id: str) -> PurchaseResult:
        listing = self._active.get(listing_id)
        if listing is None:
            return PurchaseResult(listing_id=listing_id, success=False, price_paid=0, message="Listing no longer available")
        del self._active[listing_id]
        self._binder[listing.card_id] = self._binder.get(listing.card_id, 0) + 1
        return PurchaseResult(listing_id=listing_id, success=True, price_paid=listing.buy_now, message="Purchased")

    async def list_card(
        self, card_id: str, buy_now_price: int, start_bid: int, duration_seconds: int
    ) -> ListResult:
        owned = self._binder.get(card_id, 0)
        if owned <= 0:
            return ListResult(card_id=card_id, success=False, listing_id=None, message="Card not in binder")

        cards_by_id = {cid: (name, ovr, program, position, team) for cid, name, ovr, program, position, team in _CARD_POOL}
        if card_id not in cards_by_id:
            return ListResult(card_id=card_id, success=False, listing_id=None, message="Unknown card")

        self._binder[card_id] = owned - 1
        name, ovr, program, position, team = cards_by_id[card_id]
        listing_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        self._active[listing_id] = Listing(
            listing_id=listing_id,
            card_id=card_id,
            card_name=name,
            ovr=ovr,
            program=program,
            position=position,
            team=team,
            buy_now=buy_now_price,
            current_bid=start_bid,
            expires_at=now + timedelta(seconds=duration_seconds),
        )
        return ListResult(card_id=card_id, success=True, listing_id=listing_id, message="Listed")

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
