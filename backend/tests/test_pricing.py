from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app import pricing

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def obs(price: int, hours_ago: float) -> pricing.PriceObservation:
    return pricing.PriceObservation(price=price, observed_at=NOW - timedelta(hours=hours_ago))


def test_not_priceable_below_min_samples():
    observations = [obs(100_000, 1) for _ in range(7)]
    estimate = pricing.estimate_value("card1", observations, now=NOW, min_samples=8)
    assert not estimate.priceable
    assert estimate.sample_count == 7
    assert estimate.est_value is None


def test_priceable_at_min_samples():
    observations = [obs(100_000, 1) for _ in range(8)]
    estimate = pricing.estimate_value("card1", observations, now=NOW, min_samples=8)
    assert estimate.priceable
    assert estimate.sample_count == 8
    assert estimate.median_price == 100_000


def test_window_excludes_old_observations():
    recent = [obs(100_000, 1) for _ in range(8)]
    stale = [obs(500_000, 100) for _ in range(8)]  # outside a 6h window
    estimate = pricing.estimate_value("card1", recent + stale, now=NOW, window_hours=6, min_samples=8)
    assert estimate.sample_count == 8
    assert estimate.median_price == 100_000


def test_est_value_applies_tax():
    observations = [obs(100_000, 1) for _ in range(8)]
    estimate = pricing.estimate_value("card1", observations, now=NOW, min_samples=8, ah_tax_rate=0.10)
    assert estimate.est_value == pytest.approx(90_000)


def test_est_value_uses_median_not_mean():
    prices = [10_000, 20_000, 30_000, 1_000_000, 40_000, 50_000, 60_000, 70_000]
    observations = [obs(p, 1) for p in prices]
    estimate = pricing.estimate_value("card1", observations, now=NOW, min_samples=8, ah_tax_rate=0)
    # median of the sorted list, not skewed by the 1,000,000 outlier
    assert estimate.median_price == 45_000


def test_is_snipe_true_at_threshold_boundary():
    # buy_now exactly at the threshold counts as a snipe ("<=")
    assert pricing.is_snipe(buy_now=75_000, est_value=100_000, margin_threshold=0.25)


def test_is_snipe_false_just_above_threshold():
    assert not pricing.is_snipe(buy_now=75_001, est_value=100_000, margin_threshold=0.25)


def test_is_snipe_false_for_non_positive_inputs():
    assert not pricing.is_snipe(buy_now=0, est_value=100_000)
    assert not pricing.is_snipe(buy_now=50_000, est_value=0)


def test_margin_calculation():
    margin_coins, margin_pct = pricing.margin(buy_now=75_000, est_value=100_000)
    assert margin_coins == 25_000
    assert margin_pct == pytest.approx(0.25)
