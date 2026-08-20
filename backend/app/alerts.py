from __future__ import annotations

import logging

import httpx

from . import schemas

logger = logging.getLogger("mutsniper.alerts")


async def notify_discord(webhook_url: str, snipe: schemas.SnipeOut) -> None:
    if not webhook_url:
        return
    content = (
        f"SNIPE: {snipe.card_name} ({snipe.program} {snipe.ovr} OVR) - "
        f"buy now {snipe.buy_now:,} vs est value {snipe.est_value:,.0f} "
        f"({snipe.margin_pct:.0%} margin)"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as http_client:
            await http_client.post(webhook_url, json={"content": content})
    except httpx.HTTPError:
        logger.exception("Failed to post Discord alert")
