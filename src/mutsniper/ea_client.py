from __future__ import annotations

import time

from playwright.sync_api import BrowserContext

from .models import Listing

CARD_DATABASE_URL = (
    "https://www.easports.com/madden-nfl/ultimate-team/web-app/data/1/cards/player"
)


def fetch_card_database(context: BrowserContext, name: str | None = None) -> list[dict]:
    """Public, unauthenticated card reference data (ratings, ids, etc).
    Confirmed live; useful for resolving a player name to a card_id."""
    params = {}
    if name:
        params["name"] = name
    response = context.request.get(CARD_DATABASE_URL, params=params)
    if not response.ok:
        raise RuntimeError(f"Card database request failed: {response.status}")
    return response.json()


def search_auctions(context: BrowserContext, player_query: str, seen_ts: int | None = None) -> list[Listing]:
    """Live auction house search for a player. NOT YET WIRED UP.

    The auction search endpoint requires an authenticated session and its
    path/params/response shape aren't publicly documented anywhere - every
    real MUT tool gets this by capturing one real request from a logged-in
    browser session. To finish this:

      1. Run `mutsniper login` and complete the EA login.
      2. In that same browser (or Chrome devtools against the web app),
         search the auction house for a player.
      3. Grab the XHR request to the auction search endpoint: right-click
         it in the Network tab -> Copy -> Copy as cURL, and grab one
         sample JSON response body too.
      4. Send both over - this function gets rewritten to hit the real
         endpoint and map its fields into `Listing` (auction_id, card_id,
         card_name, quality, ovr, position, team, start_bid,
         buy_now_price, current_bid, expiry_ts).

    Until then this raises so a misconfigured scan fails loudly instead of
    silently reporting zero listings as "market is quiet".
    """
    raise NotImplementedError(
        "search_auctions is not wired up yet - see the docstring for what's needed."
    )
