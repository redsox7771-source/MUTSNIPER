from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Card(Base):
    __tablename__ = "cards"

    card_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    ovr: Mapped[int] = mapped_column(Integer)
    program: Mapped[str] = mapped_column(String)
    position: Mapped[str] = mapped_column(String)
    team: Mapped[str] = mapped_column(String)


class Listing(Base):
    __tablename__ = "listings"

    listing_id: Mapped[str] = mapped_column(String, primary_key=True)
    card_id: Mapped[str] = mapped_column(String, ForeignKey("cards.card_id"), index=True)
    buy_now: Mapped[int] = mapped_column(BigInteger)
    current_bid: Mapped[int] = mapped_column(BigInteger)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # "active" while still seen in polls. When a previously-active listing
    # stops showing up, it's reconciled to "sold" (disappeared before its
    # own expires_at - someone bought it) or "cancelled" (reached its
    # expiry, or was pulled, without a buyer) - see
    # repository.upsert_listings.
    status: Mapped[str] = mapped_column(String, default="active", index=True)


class PricePoint(Base):
    __tablename__ = "price_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[str] = mapped_column(String, ForeignKey("cards.card_id"), index=True)
    price: Mapped[int] = mapped_column(BigInteger)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source: Mapped[str] = mapped_column(String)


class Snipe(Base):
    __tablename__ = "snipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[str] = mapped_column(String, ForeignKey("listings.listing_id"), index=True)
    card_id: Mapped[str] = mapped_column(String, ForeignKey("cards.card_id"), index=True)
    buy_now: Mapped[int] = mapped_column(BigInteger)
    est_value: Mapped[float] = mapped_column(Float)
    margin: Mapped[float] = mapped_column(Float)
    margin_pct: Mapped[float] = mapped_column(Float)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[str] = mapped_column(String, index=True)
    card_id: Mapped[str] = mapped_column(String, index=True)
    price_paid: Mapped[int] = mapped_column(BigInteger)
    success: Mapped[bool] = mapped_column()
    message: Mapped[str] = mapped_column(String)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
