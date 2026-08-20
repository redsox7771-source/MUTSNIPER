from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import poller, repository, schemas
from .config import settings
from .db import SessionLocal, init_models
from .ea_client.base import EAClient, ListingFilter
from .ea_client.mock import MockEAClient
from .ea_client.real import RealEAClient
from .ws import ConnectionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ws_manager = ConnectionManager()


def _build_client():
    if settings.ea_client == "real":
        return RealEAClient(settings)
    return MockEAClient()


def _build_filters() -> list[ListingFilter]:
    raw = json.loads(settings.watchlist_json)
    if not raw:
        return [ListingFilter()]
    return [ListingFilter(**f) for f in raw]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    client = _build_client()
    app.state.ea_client = client
    filters = _build_filters()
    task = asyncio.create_task(poller.run(client, filters, settings, SessionLocal, ws_manager))
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="mutsniper", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/snipes", response_model=list[schemas.SnipeOut])
async def get_snipes(
    min_margin_pct: float = Query(0.0, ge=0, le=1),
    min_ovr: int | None = None,
    program: str | None = None,
    limit: int = Query(100, le=500),
):
    async with SessionLocal() as session:
        return await repository.list_snipes(
            session, min_margin_pct=min_margin_pct, min_ovr=min_ovr, program=program, limit=limit
        )


@app.get("/cards/{card_id}/price-history", response_model=list[schemas.PriceHistoryPoint])
async def get_price_history(card_id: str, hours: int = 24):
    async with SessionLocal() as session:
        return await repository.price_history(session, card_id, hours)


@app.websocket("/ws/feed")
async def ws_feed(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


class ConfirmedRequest(BaseModel):
    confirm: bool = False


def _require_confirm(confirm: bool) -> None:
    # Belt-and-suspenders on top of the UI's own confirmation dialog -
    # these actions spend real coins, so a bare POST without an explicit
    # confirm flag (e.g. an accidental resubmit, a stray script) is refused.
    if not confirm:
        raise HTTPException(status_code=400, detail="confirm must be true to execute a write action")


@app.post("/snipes/{listing_id}/buy", response_model=schemas.BuyResult)
async def buy_snipe(listing_id: str, body: ConfirmedRequest, request: Request):
    _require_confirm(body.confirm)
    client: EAClient = request.app.state.ea_client

    async with SessionLocal() as session:
        card_id = await repository.get_listing_card_id(session, listing_id)

    result = await client.buy_now(listing_id)

    async with SessionLocal() as session:
        await repository.record_purchase(session, card_id or "unknown", result)

    return schemas.BuyResult(**asdict(result))


@app.get("/binder", response_model=list[schemas.OwnedCardOut])
async def get_binder(request: Request):
    client: EAClient = request.app.state.ea_client
    owned = await client.get_binder()
    return [schemas.OwnedCardOut(**asdict(card)) for card in owned]


class ListCardBody(schemas.ListCardRequest, ConfirmedRequest):
    pass


@app.post("/binder/{card_id}/list", response_model=schemas.ListCardResult)
async def list_card(card_id: str, body: ListCardBody, request: Request):
    _require_confirm(body.confirm)
    client: EAClient = request.app.state.ea_client
    result = await client.list_card(card_id, body.buy_now_price, body.start_bid, body.duration_seconds)
    return schemas.ListCardResult(**asdict(result))


@app.get("/purchases", response_model=list[schemas.PurchaseOut])
async def get_purchases(limit: int = Query(100, le=500)):
    async with SessionLocal() as session:
        rows = await repository.list_purchases(session, limit)
        return [
            schemas.PurchaseOut(
                listing_id=row.listing_id,
                card_id=row.card_id,
                price_paid=row.price_paid,
                success=row.success,
                message=row.message,
                purchased_at=row.purchased_at,
            )
            for row in rows
        ]
