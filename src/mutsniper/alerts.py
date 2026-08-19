from __future__ import annotations

import logging

import requests

from .models import SnipeResult
from .snipe import listing_price

logger = logging.getLogger("mutsniper.alerts")


def _format(result: SnipeResult) -> str:
    listing = result.listing
    price = listing_price(listing)
    return (
        f"SNIPE: {listing.card_name} ({listing.quality} {listing.ovr} OVR) "
        f"listed at {price:,} coins vs. median {result.market_median:,.0f} "
        f"({result.discount_pct:.0%} below, n={result.sample_count})"
    )


def notify_console(result: SnipeResult) -> None:
    logger.warning(_format(result))


def notify_discord(webhook_url: str, result: SnipeResult) -> None:
    if not webhook_url:
        return
    try:
        requests.post(webhook_url, json={"content": _format(result)}, timeout=10)
    except requests.RequestException:
        logger.exception("Failed to post Discord alert")


def notify_desktop(result: SnipeResult) -> None:
    try:
        from plyer import notification
    except ImportError:
        return
    try:
        notification.notify(
            title="MUT snipe found",
            message=_format(result),
            timeout=15,
        )
    except Exception:
        logger.exception("Failed to show desktop notification")


def dispatch(result: SnipeResult, discord_webhook_url: str = "") -> None:
    notify_console(result)
    notify_desktop(result)
    notify_discord(discord_webhook_url, result)
