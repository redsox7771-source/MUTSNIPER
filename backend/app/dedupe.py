from __future__ import annotations

from dataclasses import dataclass

from .ea_client.base import Listing


@dataclass(frozen=True)
class DedupeResult:
    new: list[Listing]
    updated: list[Listing]


def dedupe_listings(existing_ids: set[str], incoming: list[Listing]) -> DedupeResult:
    """Split a batch of incoming listings into new vs already-known by
    listing_id. Pure function, no DB - callers decide what to do with the
    result."""
    new: list[Listing] = []
    updated: list[Listing] = []
    seen_in_batch: set[str] = set()

    for listing in incoming:
        if listing.listing_id in seen_in_batch:
            continue  # duplicate within the same batch, keep the first occurrence
        seen_in_batch.add(listing.listing_id)

        if listing.listing_id in existing_ids:
            updated.append(listing)
        else:
            new.append(listing)

    return DedupeResult(new=new, updated=updated)
