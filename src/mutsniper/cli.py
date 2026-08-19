from __future__ import annotations

import argparse
import logging

from . import auth, db
from .config import CONFIG


def cmd_login(args: argparse.Namespace) -> None:
    auth.login(CONFIG.session_path)


def cmd_scan(args: argparse.Namespace) -> None:
    from . import scanner

    scanner.run(CONFIG)


def cmd_stats(args: argparse.Namespace) -> None:
    stats = db.market_stats(CONFIG.db_path, args.card_id, CONFIG.lookback_hours)
    if stats.sample_count == 0:
        print(f"No sold-auction history yet for card_id={args.card_id}")
        return
    print(
        f"card_id={args.card_id}  median={stats.median_price:,.0f}  "
        f"n={stats.sample_count} (last {CONFIG.lookback_hours}h)"
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(prog="mutsniper")
    subparsers = parser.add_subparsers(required=True)

    login_parser = subparsers.add_parser("login", help="Capture an EA web app session")
    login_parser.set_defaults(func=cmd_login)

    scan_parser = subparsers.add_parser("scan", help="Run the continuous snipe scanner")
    scan_parser.set_defaults(func=cmd_scan)

    stats_parser = subparsers.add_parser("stats", help="Show market stats for a card_id")
    stats_parser.add_argument("card_id")
    stats_parser.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
