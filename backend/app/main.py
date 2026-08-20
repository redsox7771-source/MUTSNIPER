from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from . import poller, repository, schemas
from .config import settings
from .db import SessionLocal, init_models
from .ea_client.base import ListingFilter
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
