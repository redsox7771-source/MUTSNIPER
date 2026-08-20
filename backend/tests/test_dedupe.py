from __future__ import annotations

from datetime import datetime, timezone

from app.dedupe import dedupe_listings
from app.ea_client.base import Listing


def make_listing(listing_id: str, buy_now: int = 100_000) -> Listing:
    return Listing(
        listing_id=listing_id,
        card_id="card1",
        card_name="Test Card",
        ovr=90,
        program="Core",
        position="WR",
        team="XYZ",
        buy_now=buy_now,
        current_bid=buy_now,
        expires_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
    )


def test_all_new_when_no_existing():
    incoming = [make_listing("a1"), make_listing("a2")]
    result = dedupe_listings(existing_ids=set(), incoming=incoming)
    assert {l.listing_id for l in result.new} == {"a1", "a2"}
    assert result.updated == []


def test_all_updated_when_all_existing():
    incoming = [make_listing("a1"), make_listing("a2")]
    result = dedupe_listings(existing_ids={"a1", "a2"}, incoming=incoming)
    assert result.new == []
    assert {l.listing_id for l in result.updated} == {"a1", "a2"}


def test_mixed_new_and_updated():
    incoming = [make_listing("a1"), make_listing("a2"), make_listing("a3")]
    result = dedupe_listings(existing_ids={"a2"}, incoming=incoming)
    assert {l.listing_id for l in result.new} == {"a1", "a3"}
    assert {l.listing_id for l in result.updated} == {"a2"}


def test_within_batch_duplicate_keeps_first_occurrence():
    incoming = [make_listing("a1", buy_now=100_000), make_listing("a1", buy_now=999_999)]
    result = dedupe_listings(existing_ids=set(), incoming=incoming)
    assert len(result.new) == 1
    assert result.new[0].buy_now == 100_000


def test_empty_incoming_produces_empty_result():
    result = dedupe_listings(existing_ids={"a1"}, incoming=[])
    assert result.new == []
    assert result.updated == []
