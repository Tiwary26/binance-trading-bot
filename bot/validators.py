"""
validators.py
~~~~~~~~~~~~~
Input validation for order parameters.
Raises ValueError with descriptive messages on invalid input.
"""

from __future__ import annotations

from typing import Optional
from .logging_config import get_logger

logger = get_logger("validators")

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

MIN_QUANTITY = 0.001
MAX_QUANTITY = 1_000_000.0
MIN_PRICE = 0.01
MAX_PRICE = 10_000_000.0


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise a futures trading symbol.

    Rules:
      - Must be a non-empty string.
      - Uppercased.
      - Must end with 'USDT' (USDT-M futures only).
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("symbol must be a non-empty string (e.g. BTCUSDT).")
    symbol = symbol.strip().upper()
    if not symbol.endswith("USDT"):
        raise ValueError(
            f"Invalid symbol '{symbol}'. "
            "Only USDT-M perpetual futures are supported (e.g. BTCUSDT, ETHUSDT)."
        )
    logger.debug("Symbol validated: %s", symbol)
    return symbol


def validate_side(side: str) -> str:
    """Validate order side: BUY or SELL."""
    if not side or not isinstance(side, str):
        raise ValueError("side must be 'BUY' or 'SELL'.")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Allowed values: {', '.join(sorted(VALID_SIDES))}."
        )
    logger.debug("Side validated: %s", side)
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type: MARKET or LIMIT."""
    if not order_type or not isinstance(order_type, str):
        raise ValueError("order_type must be 'MARKET' or 'LIMIT'.")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Allowed values: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    logger.debug("Order type validated: %s", order_type)
    return order_type


def validate_quantity(quantity: float | str) -> float:
    """
    Validate order quantity.

    Rules:
      - Must be a positive number.
      - Between MIN_QUANTITY and MAX_QUANTITY.
    """
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"quantity must be a number, got: '{quantity}'.")
    if quantity <= 0:
        raise ValueError(f"quantity must be positive, got: {quantity}.")
    if quantity < MIN_QUANTITY:
        raise ValueError(
            f"quantity {quantity} is below the minimum allowed ({MIN_QUANTITY})."
        )
    if quantity > MAX_QUANTITY:
        raise ValueError(
            f"quantity {quantity} exceeds the maximum allowed ({MAX_QUANTITY})."
        )
    logger.debug("Quantity validated: %s", quantity)
    return quantity


def validate_price(price: float | str | None, order_type: str) -> Optional[float]:
    """
    Validate price field.

    Rules:
      - Required and positive for LIMIT orders.
      - Must be None / omitted for MARKET orders.
    """
    if order_type == "LIMIT":
        if price is None:
            raise ValueError("price is required for LIMIT orders.")
        try:
            price = float(price)
        except (TypeError, ValueError):
            raise ValueError(f"price must be a number, got: '{price}'.")
        if price <= 0:
            raise ValueError(f"price must be positive, got: {price}.")
        if price < MIN_PRICE:
            raise ValueError(
                f"price {price} is below the minimum allowed ({MIN_PRICE})."
            )
        if price > MAX_PRICE:
            raise ValueError(
                f"price {price} exceeds the maximum allowed ({MAX_PRICE})."
            )
        logger.debug("Price validated: %s", price)
        return price

    if order_type == "MARKET" and price is not None:
        logger.warning(
            "price parameter is ignored for MARKET orders and will not be sent."
        )
    return None


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float | str,
    price: float | str | None = None,
) -> dict:
    """
    Run all validations and return a clean, normalised parameter dict.

    Returns:
        {
            "symbol": str,
            "side": str,
            "order_type": str,
            "quantity": float,
            "price": float | None,
        }
    """
    clean = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
    }
    clean["price"] = validate_price(price, clean["order_type"])
    logger.info(
        "All parameters validated — symbol=%s side=%s type=%s qty=%s price=%s",
        clean["symbol"],
        clean["side"],
        clean["order_type"],
        clean["quantity"],
        clean["price"],
    )
    return clean
