from __future__ import annotations

import asyncio
import logging
import random
import time
from collections import deque
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker

from . import alerts, pricing, repository, schemas
from .config import Settings
from .ea_client.base import EAAuthError, EAClient, EARateLimitError, EAServerError, Listing, ListingFilter
from .ws import ConnectionManager

logger = logging.getLogger("mutsniper.poller")


class RateLimiter:
    """Hard cap on requests per rolling 60s window, shared across every
    filter set the poller cycles through."""

    def __init__(self, max_per_minute: int) -> None:
        self._max = max_per_minute
        self._timestamps: deque[float] = deque()

    async def acquire(self) -> None:
        while True:
            now = time.monotonic()
            while self._timestamps and now - self._timestamps[0] > 60:
                self._timestamps.popleft()
            if len(self._timestamps) < self._max:
                self._timestamps.append(now)
                return
            await asyncio.sleep(60 - (now - self._timestamps[0]))


async def run(
    client: EAClient,
    filters: list[ListingFilter],
    settings: Settings,
    session_factory: async_sessionmaker,
    ws_manager: ConnectionManager,
) -> None:
    rate_limiter = RateLimiter(settings.poll_rate_cap_per_minute)
    backoff_seconds = 1.0

    while True:
        for listing_filter in filters:
            await rate_limiter.acquire()
            try:
                listings = await client.search_listings(listing_filter)
            except EAAuthError:
                logger.error("EA session rejected (401) - refresh MUTSNIPER_EA_TOKEN in .env")
                await asyncio.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 300)
                continue
            except (EARateLimitError, EAServerError) as exc:
                logger.warning("%s from EA, backing off %.0fs", type(exc).__name__, backoff_seconds)
                await asyncio.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 300)
                continue
            except Exception:
                logger.exception("Unexpected error fetching listings for filter %r", listing_filter)
                continue

            backoff_seconds = 1.0
            await _process_batch(listings, settings, session_factory, ws_manager)

            await asyncio.sleep(
                random.uniform(settings.poll_interval_min_seconds, settings.poll_interval_max_seconds)
            )


async def _process_batch(
    listings: list[Listing],
    settings: Settings,
    session_factory: async_sessionmaker,
    ws_manager: ConnectionManager,
) -> None:
    if not listings:
        return

    async with session_factory() as session:
        new_count, updated_count = await repository.upsert_listings(session, listings)
        logger.info("Poll: %d new, %d updated", new_count, updated_count)

        now = datetime.now(timezone.utc)
        for listing in listings:
            observations = await repository.recent_price_observations(
                session, listing.card_id, window_hours=settings.price_window_hours
            )
            estimate = pricing.estimate_value(
                listing.card_id,
                observations,
                now=now,
                window_hours=settings.price_window_hours,
                min_samples=settings.price_min_samples,
                ah_tax_rate=settings.ah_tax_rate,
            )
            if not estimate.priceable:
                continue
            if not pricing.is_snipe(listing.buy_now, estimate.est_value, settings.snipe_margin_threshold):
                continue

            margin_coins, margin_pct = pricing.margin(listing.buy_now, estimate.est_value)
            recorded = await repository.record_snipe_if_new(
                session, listing, estimate.est_value, margin_coins, margin_pct, now
            )
            if recorded is None:
                continue  # already flagged on an earlier poll - don't re-broadcast/re-alert

            snipe_out = schemas.SnipeOut(
                listing_id=listing.listing_id,
                card_id=listing.card_id,
                card_name=listing.card_name,
                ovr=listing.ovr,
                program=listing.program,
                position=listing.position,
                buy_now=listing.buy_now,
                est_value=estimate.est_value,
                margin=margin_coins,
                margin_pct=margin_pct,
                expires_at=listing.expires_at,
                detected_at=now,
            )
            await ws_manager.broadcast(snipe_out)
            if settings.discord_alerts_enabled:
                await alerts.notify_discord(settings.discord_webhook_url, snipe_out)
