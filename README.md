# mutsniper

Continuous scanner for the Madden Ultimate Team auction house. Polls a
watchlist of players, builds its own sold-price history (MUT doesn't expose
one), and alerts when a new listing is priced well below the recent median.

## Status

Scaffolding is done: session auth, price-history DB, snipe scoring, and
alerting all work. `ea_client.search_auctions` (the live auction search
call) is **not wired up yet** - see the docstring in
`src/mutsniper/ea_client.py` for exactly what's needed to finish it.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
playwright install chromium
cp .env.example .env   # then edit: set MUTSNIPER_WATCHLIST at minimum
```

## Usage

```bash
mutsniper login   # opens a browser, log into EA, then press Enter
mutsniper scan    # runs the continuous scanner
mutsniper stats <card_id>   # check the market price we've built for a card
```

## How snipe detection works

Every poll, active auctions are upserted into SQLite keyed by `auction_id`.
When a previously-active auction disappears *before* its listed expiry
time, that's treated as a sale, and its last-seen price is recorded. The
rolling median of a card's recent sales (`MUTSNIPER_LOOKBACK_HOURS`) is its
market price; a new listing priced `MUTSNIPER_SNIPE_THRESHOLD_PCT` or more
below that median triggers an alert - but only once at least
`MUTSNIPER_MIN_SAMPLES` sales have been observed, so low-liquidity cards
with one weird sale don't produce false positives.
