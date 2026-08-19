from __future__ import annotations

from . import db
from .models import Listing, MarketStats, SnipeResult


def listing_price(listing: Listing) -> int:
    """The price you'd actually pay right now: Buy Now if set, else the
    current bid (a proxy for a live auction with no BIN)."""
    return listing.buy_now_price or listing.current_bid


def evaluate(
    listing: Listing,
    stats: MarketStats,
    threshold_pct: float,
    min_samples: int,
) -> SnipeResult | None:
    if stats.sample_count < min_samples or stats.median_price <= 0:
        return None

    price = listing_price(listing)
    if price <= 0:
        return None

    discount_pct = 1 - (price / stats.median_price)
    if discount_pct < threshold_pct:
        return None

    return SnipeResult(
        listing=listing,
        market_median=stats.median_price,
        discount_pct=discount_pct,
        sample_count=stats.sample_count,
    )


def find_snipes(
    db_path: str,
    listings: list[Listing],
    threshold_pct: float,
    min_samples: int,
    lookback_hours: int,
) -> list[SnipeResult]:
    results = []
    stats_cache: dict[str, MarketStats] = {}

    for listing in listings:
        stats = stats_cache.get(listing.card_id)
        if stats is None:
            stats = db.market_stats(db_path, listing.card_id, lookback_hours)
            stats_cache[listing.card_id] = stats

        result = evaluate(listing, stats, threshold_pct, min_samples)
        if result is not None:
            results.append(result)

    return results
