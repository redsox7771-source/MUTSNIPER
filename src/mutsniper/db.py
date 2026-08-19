from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from statistics import median

from .models import Listing, MarketStats

SCHEMA = """
CREATE TABLE IF NOT EXISTS auctions (
    auction_id TEXT PRIMARY KEY,
    card_id TEXT NOT NULL,
    card_name TEXT,
    quality TEXT,
    ovr INTEGER,
    position TEXT,
    team TEXT,
    start_bid INTEGER,
    buy_now_price INTEGER,
    current_bid INTEGER,
    expiry_ts INTEGER,
    first_seen_ts INTEGER NOT NULL,
    last_seen_ts INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    sold_price INTEGER
);
CREATE INDEX IF NOT EXISTS idx_auctions_card ON auctions(card_id);
CREATE INDEX IF NOT EXISTS idx_auctions_status ON auctions(status);
"""


@contextmanager
def connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


def _sold_price_estimate(start_bid: int, current_bid: int, buy_now_price: int) -> int:
    # An auction that disappeared before its expiry was won. If it never
    # drew a bid above the opening price, it almost certainly went via
    # Buy Now rather than a last-second bid at the floor.
    if current_bid > start_bid:
        return current_bid
    if buy_now_price:
        return buy_now_price
    return current_bid


def record_snapshot(db_path: str, listings: list[Listing]) -> None:
    """Upsert the current poll's listings and mark any previously-active
    auction that's now missing as sold (if it vanished early) or expired."""
    now = int(time.time())
    seen_ids = {listing.auction_id for listing in listings}

    with connect(db_path) as conn:
        for listing in listings:
            conn.execute(
                """
                INSERT INTO auctions (
                    auction_id, card_id, card_name, quality, ovr, position, team,
                    start_bid, buy_now_price, current_bid, expiry_ts,
                    first_seen_ts, last_seen_ts, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
                ON CONFLICT(auction_id) DO UPDATE SET
                    current_bid = excluded.current_bid,
                    buy_now_price = excluded.buy_now_price,
                    last_seen_ts = excluded.last_seen_ts
                """,
                (
                    listing.auction_id, listing.card_id, listing.card_name,
                    listing.quality, listing.ovr, listing.position, listing.team,
                    listing.start_bid, listing.buy_now_price, listing.current_bid,
                    listing.expiry_ts, listing.seen_ts, listing.seen_ts,
                ),
            )

        card_ids = {listing.card_id for listing in listings}
        if not card_ids:
            return
        placeholders = ",".join("?" for _ in card_ids)
        rows = conn.execute(
            f"SELECT * FROM auctions WHERE status = 'active' AND card_id IN ({placeholders})",
            tuple(card_ids),
        ).fetchall()

        for row in rows:
            if row["auction_id"] in seen_ids:
                continue
            if row["expiry_ts"] and row["expiry_ts"] > now:
                sold_price = _sold_price_estimate(
                    row["start_bid"], row["current_bid"], row["buy_now_price"]
                )
                conn.execute(
                    "UPDATE auctions SET status = 'sold', sold_price = ? WHERE auction_id = ?",
                    (sold_price, row["auction_id"]),
                )
            else:
                conn.execute(
                    "UPDATE auctions SET status = 'expired_unsold' WHERE auction_id = ?",
                    (row["auction_id"],),
                )


def market_stats(db_path: str, card_id: str, lookback_hours: int) -> MarketStats:
    cutoff = int(time.time()) - lookback_hours * 3600
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT sold_price FROM auctions "
            "WHERE card_id = ? AND status = 'sold' AND last_seen_ts >= ?",
            (card_id, cutoff),
        ).fetchall()
    prices = [row["sold_price"] for row in rows if row["sold_price"]]
    if not prices:
        return MarketStats(card_id=card_id, median_price=0.0, sample_count=0)
    return MarketStats(card_id=card_id, median_price=median(prices), sample_count=len(prices))


def active_listings(db_path: str, card_id: str) -> list[sqlite3.Row]:
    with connect(db_path) as conn:
        return conn.execute(
            "SELECT * FROM auctions WHERE card_id = ? AND status = 'active'",
            (card_id,),
        ).fetchall()
