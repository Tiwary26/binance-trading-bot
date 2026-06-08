"""
cli.py
~~~~~~
Command-line entry point for the Binance Futures Testnet trading bot.

Usage examples
--------------
Place a MARKET BUY:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

Place a LIMIT SELL:
    python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500.00

Use environment variables for credentials (recommended):
    export BINANCE_API_KEY=your_key
    export BINANCE_API_SECRET=your_secret
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

Or pass them directly (not recommended in shared environments):
    python cli.py --api-key <key> --api-secret <secret> ...
"""

from __future__ import annotations

import argparse
import os
import sys

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logging, get_logger
from bot.orders import OrderPlacer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    creds = parser.add_argument_group("API credentials")
    creds.add_argument(
        "--api-key",
        default=os.environ.get("BINANCE_API_KEY", ""),
        help="Binance Futures Testnet API key "
             "(default: $BINANCE_API_KEY env var).",
    )
    creds.add_argument(
        "--api-secret",
        default=os.environ.get("BINANCE_API_SECRET", ""),
        help="Binance Futures Testnet API secret "
             "(default: $BINANCE_API_SECRET env var).",
    )

    order = parser.add_argument_group("Order parameters")
    order.add_argument(
        "--symbol",
        required=True,
        metavar="SYMBOL",
        help="Trading pair, e.g. BTCUSDT.",
    )
    order.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        type=str.upper,
        metavar="SIDE",
        help="Order side: BUY or SELL.",
    )
    order.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT"],
        type=str.upper,
        metavar="TYPE",
        help="Order type: MARKET or LIMIT.",
    )
    order.add_argument(
        "--quantity",
        required=True,
        type=float,
        metavar="QTY",
        help="Order quantity in base asset units (e.g. 0.001 BTC).",
    )
    order.add_argument(
        "--price",
        type=float,
        default=None,
        metavar="PRICE",
        help="Limit price in USDT. Required for LIMIT orders, ignored for MARKET.",
    )

    misc = parser.add_argument_group("Miscellaneous")
    misc.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        type=str.upper,
        help="Console log level (default: INFO). File always logs at DEBUG.",
    )
    misc.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print the request summary without sending to the API.",
    )

    return parser


def print_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
) -> None:
    """Print the order request details before sending."""
    print()
    print("=" * 55)
    print("  ORDER REQUEST SUMMARY")
    print("=" * 55)
    print(f"  Symbol       : {symbol.upper()}")
    print(f"  Side         : {side.upper()}")
    print(f"  Order Type   : {order_type.upper()}")
    print(f"  Quantity     : {quantity}")
    if price is not None:
        print(f"  Price        : {price}")
    print("=" * 55)
    print()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logging(level=args.log_level)
    logger = get_logger("cli")

    logger.info(
        "CLI invoked — symbol=%s side=%s type=%s qty=%s price=%s dry_run=%s",
        args.symbol,
        args.side,
        args.order_type,
        args.quantity,
        args.price,
        args.dry_run,
    )

    print_request_summary(
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
    )

    if args.dry_run:
        print("[DRY RUN] Inputs validated. No API credentials required. No order was sent.")
        logger.info("Dry-run mode — no order sent.")
        return 0

    if not args.api_key or not args.api_secret:
        print(
            "\n[ERROR] API credentials are required for live order execution.\n"
            "Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables,\n"
            "or pass --api-key / --api-secret on the command line.\n"
            "Tip: use --dry-run to validate inputs without credentials.\n",
            file=sys.stderr,
        )
        logger.error("Missing API credentials. Aborting.")
        return 1

    try:
        client = BinanceFuturesClient(
            api_key=args.api_key,
            api_secret=args.api_secret,
        )
    except ValueError as exc:
        print(f"\n[ERROR] Could not initialise client: {exc}\n", file=sys.stderr)
        logger.error("Client init error: %s", exc)
        return 1

    placer = OrderPlacer(client)
    result = placer.place_order(
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
    )

    print()
    print("  ORDER RESPONSE")
    print(result.summary())

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
