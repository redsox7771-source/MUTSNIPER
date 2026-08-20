from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, pricing
from .dedupe import dedupe_listings
from .ea_client.base import Listing as EAListing
from .ea_client.base import PurchaseResult


# How long a previously-active listing must go unseen, for a card this
# poll actually searched, before we conclude it's really gone rather than
# just missed by one poll cycle (pagination hiccup, transient API miss).
_RECONCILE_GRACE = timedelta(seconds=60)


async def upsert_listings(session: AsyncSession, listings: list[EAListing]) -> tuple[int, int]:
    """Upsert a poll batch by listing_id, log a price_point for every
    sighting, and reconcile any previously-active listing for the same
    cards that didn't show up this time: sold if it vanished before its
    own expiry, cancelled if it reached expiry (or was pulled) unsold."""
    if not listings:
        return 0, 0

    now = datetime.now(timezone.utc)
    listing_ids = [listing.listing_id for listing in listings]
    existing_rows = await session.execute(
        select(models.Listing.listing_id).where(models.Listing.listing_id.in_(listing_ids))
    )
    existing_ids = {row[0] for row in existing_rows}

    result = dedupe_listings(existing_ids, listings)

    for listing in result.new:
        await _ensure_card(session, listing)
        session.add(
            models.Listing(
                listing_id=listing.listing_id,
                card_id=listing.card_id,
                buy_now=listing.buy_now,
                current_bid=listing.current_bid,
                expires_at=listing.expires_at,
                first_seen=now,
                last_seen=now,
                status="active",
            )
        )

    for listing in result.updated:
        await session.execute(
            update(models.Listing)
            .where(models.Listing.listing_id == listing.listing_id)
            .values(buy_now=listing.buy_now, current_bid=listing.current_bid, last_seen=now)
        )

    for listing in listings:
        session.add(
            models.PricePoint(
                card_id=listing.card_id,
                price=listing.buy_now,
                observed_at=now,
                source="listing_scan",
            )
        )

    seen_ids = {listing.listing_id for listing in listings}
    card_ids = {listing.card_id for listing in listings}
    stale_active = await session.execute(
        select(models.Listing).where(
            models.Listing.card_id.in_(card_ids),
            models.Listing.status == "active",
            models.Listing.last_seen <= now - _RECONCILE_GRACE,
        )
    )
    for row in stale_active.scalars():
        if row.listing_id in seen_ids:
            continue
        # The last poll to see a still-active listing is always a few
        # seconds before its exact expiry, just from poll timing - so
        # "expires_at > last_seen" alone is true for nearly every listing,
        # including ones that simply ran out the clock normally. Only
        # count it as sold if there was meaningfully more time left
        # (more than one reconcile window) when it disappeared.
        row.status = "sold" if row.expires_at - row.last_seen > _RECONCILE_GRACE else "cancelled"

    await session.commit()
    return len(result.new), len(result.updated)


async def _ensure_card(session: AsyncSession, listing: EAListing) -> None:
    existing = await session.get(models.Card, listing.card_id)
    if existing is None:
        session.add(
            models.Card(
                card_id=listing.card_id,
                name=listing.card_name,
                ovr=listing.ovr,
                program=listing.program,
                position=listing.position,
                team=listing.team,
            )
        )


async def recent_price_observations(
    session: AsyncSession, card_id: str, window_hours: int
) -> list[pricing.PriceObservation]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    rows = await session.execute(
        select(models.PricePoint.price, models.PricePoint.observed_at).where(
            models.PricePoint.card_id == card_id,
            models.PricePoint.observed_at >= cutoff,
        )
    )
    return [pricing.PriceObservation(price=row.price, observed_at=row.observed_at) for row in rows]


async def record_snipe_if_new(
    session: AsyncSession,
    listing: EAListing,
    est_value: float,
    margin_coins: float,
    margin_pct: float,
    detected_at: datetime,
) -> models.Snipe | None:
    """Record a snipe the first time a listing qualifies. A still-active
    listing re-qualifies on every poll (its price hasn't changed), so
    without this check we'd insert a duplicate row - and re-broadcast /
    re-alert - every single cycle until it sells or expires."""
    already_flagged = await session.scalar(
        select(models.Snipe.id).where(models.Snipe.listing_id == listing.listing_id).limit(1)
    )
    if already_flagged is not None:
        return None

    snipe = models.Snipe(
        listing_id=listing.listing_id,
        card_id=listing.card_id,
        buy_now=listing.buy_now,
        est_value=est_value,
        margin=margin_coins,
        margin_pct=margin_pct,
        detected_at=detected_at,
    )
    session.add(snipe)
    await session.commit()
    return snipe


async def list_snipes(
    session: AsyncSession,
    *,
    min_margin_pct: float = 0.0,
    min_ovr: int | None = None,
    program: str | None = None,
    limit: int = 100,
) -> list[dict]:
    stmt = (
        select(models.Snipe, models.Card, models.Listing)
        .join(models.Card, models.Card.card_id == models.Snipe.card_id)
        .join(models.Listing, models.Listing.listing_id == models.Snipe.listing_id)
        .where(models.Snipe.margin_pct >= min_margin_pct, models.Listing.status == "active")
        .order_by(desc(models.Snipe.detected_at))
        .limit(limit)
    )
    if min_ovr is not None:
        stmt = stmt.where(models.Card.ovr >= min_ovr)
    if program:
        stmt = stmt.where(models.Card.program == program)

    rows = await session.execute(stmt)
    return [
        {
            "listing_id": snipe.listing_id,
            "card_id": snipe.card_id,
            "card_name": card.name,
            "ovr": card.ovr,
            "program": card.program,
            "position": card.position,
            "buy_now": snipe.buy_now,
            "est_value": snipe.est_value,
            "margin": snipe.margin,
            "margin_pct": snipe.margin_pct,
            "expires_at": listing.expires_at,
            "detected_at": snipe.detected_at,
        }
        for snipe, card, listing in rows
    ]


async def price_history(session: AsyncSession, card_id: str, hours: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = await session.execute(
        select(models.PricePoint.price, models.PricePoint.observed_at, models.PricePoint.source)
        .where(models.PricePoint.card_id == card_id, models.PricePoint.observed_at >= cutoff)
        .order_by(models.PricePoint.observed_at)
    )
    return [{"price": row.price, "observed_at": row.observed_at, "source": row.source} for row in rows]


async def get_listing_card_id(session: AsyncSession, listing_id: str) -> str | None:
    listing = await session.get(models.Listing, listing_id)
    return listing.card_id if listing else None


async def record_purchase(session: AsyncSession, card_id: str, result: PurchaseResult) -> models.Purchase:
    purchase = models.Purchase(
        listing_id=result.listing_id,
        card_id=card_id,
        price_paid=result.price_paid,
        success=result.success,
        message=result.message,
        purchased_at=datetime.now(timezone.utc),
    )
    session.add(purchase)
    await session.commit()
    return purchase


async def list_purchases(session: AsyncSession, limit: int = 100) -> list[models.Purchase]:
    rows = await session.execute(
        select(models.Purchase).order_by(desc(models.Purchase.purchased_at)).limit(limit)
    )
    return list(rows.scalars())


async def recent_sales(session: AsyncSession, card_id: str, hours: int, limit: int = 20) -> list[dict]:
    """Listings reconciled to status='sold' - see upsert_listings. This is
    an inference from a listing disappearing before its own expiry, not a
    confirmed-sale record from EA (its API doesn't expose one)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = await session.execute(
        select(models.Listing)
        .where(
            models.Listing.card_id == card_id,
            models.Listing.status == "sold",
            models.Listing.last_seen >= cutoff,
        )
        .order_by(desc(models.Listing.last_seen))
        .limit(limit)
    )
    return [
        {"listing_id": row.listing_id, "price": row.buy_now, "sold_at": row.last_seen}
        for row in rows.scalars()
    ]


async def active_listings_for_card(session: AsyncSession, card_id: str, limit: int = 20) -> list[dict]:
    rows = await session.execute(
        select(models.Listing)
        .where(models.Listing.card_id == card_id, models.Listing.status == "active")
        .order_by(models.Listing.expires_at)
        .limit(limit)
    )
    return [
        {
            "listing_id": row.listing_id,
            "buy_now": row.buy_now,
            "current_bid": row.current_bid,
            "expires_at": row.expires_at,
        }
        for row in rows.scalars()
    ]
