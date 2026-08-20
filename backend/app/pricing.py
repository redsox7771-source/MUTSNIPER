from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median

AH_TAX_RATE_DEFAULT = 0.10
MARGIN_THRESHOLD_DEFAULT = 0.25
MIN_SAMPLES_DEFAULT = 8
WINDOW_HOURS_DEFAULT = 6


@dataclass(frozen=True)
class PriceObservation:
    price: int
    observed_at: datetime


@dataclass(frozen=True)
class PriceEstimate:
    card_id: str
    median_price: float | None
    sample_count: int
    est_value: float | None

    @property
    def priceable(self) -> bool:
        return self.est_value is not None


def estimate_value(
    card_id: str,
    observations: list[PriceObservation],
    *,
    now: datetime,
    window_hours: int = WINDOW_HOURS_DEFAULT,
    min_samples: int = MIN_SAMPLES_DEFAULT,
    ah_tax_rate: float = AH_TAX_RATE_DEFAULT,
) -> PriceEstimate:
    cutoff = now - timedelta(hours=window_hours)
    in_window = [o.price for o in observations if o.observed_at >= cutoff]

    if len(in_window) < min_samples:
        return PriceEstimate(card_id=card_id, median_price=None, sample_count=len(in_window), est_value=None)

    med = median(in_window)
    return PriceEstimate(
        card_id=card_id,
        median_price=med,
        sample_count=len(in_window),
        est_value=med * (1 - ah_tax_rate),
    )


def is_snipe(buy_now: int, est_value: float, margin_threshold: float = MARGIN_THRESHOLD_DEFAULT) -> bool:
    if buy_now <= 0 or est_value <= 0:
        return False
    return buy_now <= est_value * (1 - margin_threshold)


def margin(buy_now: int, est_value: float) -> tuple[float, float]:
    """Returns (margin_coins, margin_pct)."""
    margin_coins = est_value - buy_now
    margin_pct = margin_coins / est_value if est_value else 0.0
    return margin_coins, margin_pct
