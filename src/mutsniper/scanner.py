from __future__ import annotations

import logging
import time

from playwright.sync_api import sync_playwright

from . import alerts, db, ea_client, snipe
from .config import Config

logger = logging.getLogger("mutsniper.scanner")


def run(config: Config) -> None:
    if not config.watchlist:
        raise SystemExit(
            "MUTSNIPER_WATCHLIST is empty - set it to a comma-separated list "
            "of player names to watch (the auction house is searched per "
            "player, there's no global firehose)."
        )

    db.init_db(config.db_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=config.session_path)

        logger.info("Watching %d player(s), polling every %ds",
                     len(config.watchlist), config.poll_interval_seconds)

        while True:
            cycle_start = time.time()
            for player_query in config.watchlist:
                try:
                    listings = ea_client.search_auctions(
                        context, player_query, seen_ts=int(cycle_start)
                    )
                except Exception:
                    logger.exception("Failed to fetch listings for %r", player_query)
                    continue

                db.record_snapshot(config.db_path, listings)

                results = snipe.find_snipes(
                    config.db_path,
                    listings,
                    threshold_pct=config.snipe_threshold_pct,
                    min_samples=config.min_samples,
                    lookback_hours=config.lookback_hours,
                )
                for result in results:
                    alerts.dispatch(result, discord_webhook_url=config.discord_webhook_url)

            elapsed = time.time() - cycle_start
            time.sleep(max(0.0, config.poll_interval_seconds - elapsed))
