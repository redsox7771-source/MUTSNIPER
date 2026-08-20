# mutsniper

Read-only Madden Ultimate Team auction house snipe feed. Local-first,
single user. **This tool never buys, bids, lists, or sends any write
request to EA** - it only reads listings and flags the ones priced well
below recent market.

## Status

Everything works end to end against `MockEAClient` - schema, price
model, poller (dedupe, rate cap, jittered interval, backoff), FastAPI
REST + websocket feed, and the React front end have all been run and
verified live (real Postgres, real browser). The one thing left is
`RealEAClient._parse_response` in `backend/app/ea_client/real.py`, which
needs a real sample response from the actual EA endpoint - see that
file's docstring.

## Setup

```bash
docker compose up -d          # Postgres only

cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # defaults run fully on MockEAClient
uvicorn app.main:app --reload

# in a second terminal
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

The front end proxies `/api/*` and `/ws/feed` to the backend on
`:8000`, so just open `http://localhost:5173`.

## Tests

```bash
cd backend
pytest
```

Covers the price model (`pricing.py`) and the dedupe logic
(`dedupe.py`) - both are pure functions with no DB or network
dependency, so the suite runs in well under a second.

## Going live against the real auction house

1. Fill in `MUTSNIPER_EA_ENDPOINT_URL`, `MUTSNIPER_EA_HTTP_METHOD`,
   `MUTSNIPER_EA_TOKEN`, `MUTSNIPER_EA_HEADERS_JSON`, and
   `MUTSNIPER_EA_REQUEST_TEMPLATE_JSON` in `.env` with what you capture
   from the real endpoint.
2. Implement `RealEAClient._parse_response` in
   `backend/app/ea_client/real.py` against a real sample response.
3. Set `MUTSNIPER_EA_CLIENT=real`.
4. Set `MUTSNIPER_WATCHLIST_JSON` to the filter sets (OVR band,
   program, position) you actually want polled.

Everything downstream - dedupe, pricing, the API, the front end - works
identically regardless of which `EAClient` is behind it.

## How snipe detection works

Every poll batch is upserted by `listing_id` (new vs. already-seen), and
every sighting - new or existing - logs a `price_point` for that card, so
the price model has continuous signal even for listings that don't sell.
A card becomes "priceable" once it has at least
`MUTSNIPER_PRICE_MIN_SAMPLES` price points within the trailing
`MUTSNIPER_PRICE_WINDOW_HOURS`; its estimated value is the rolling
median of those, minus the `MUTSNIPER_AH_TAX_RATE` auction house tax. A
listing is flagged as a snipe once, the first time its `buy_now` price is
`MUTSNIPER_SNIPE_MARGIN_THRESHOLD` or more below that estimated value -
re-polling the same still-listed auction doesn't re-flag or re-alert it.

## Architecture

```
backend/app/
  ea_client/       EAClient interface + MockEAClient + RealEAClient
  models.py        cards, listings, price_points, snipes (SQLAlchemy)
  dedupe.py         pure new-vs-updated split by listing_id (unit tested)
  pricing.py        pure rolling-median price model (unit tested)
  repository.py     Postgres upsert/query layer built on the above
  poller.py         async loop: rate cap, jittered interval, backoff
  alerts.py          optional Discord webhook
  ws.py              websocket connection manager
  main.py            FastAPI app: REST + /ws/feed

frontend/src/
  api.ts             REST fetch + auto-reconnecting websocket client
  App.tsx            live feed state, filters, pause
  components/        SnipeFeed, SnipeRow, FilterBar, ConnectionStatus
```
