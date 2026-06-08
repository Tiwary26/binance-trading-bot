"""
orders.py
~~~~~~~~~
High-level order placement logic.

Orchestrates validation → API call → response formatting.
All public methods return an OrderResult dataclass for uniform
downstream handling in the CLI layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .client import BinanceFuturesClient, BinanceAPIError, BinanceNetworkError
from .validators import validate_order_params
from .logging_config import get_logger

logger = get_logger("orders")


@dataclass
class OrderResult:
    """Structured representation of a completed (or failed) order attempt."""

    success: bool
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]

    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    status: Optional[str] = None
    executed_qty: Optional[str] = None
    avg_price: Optional[str] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)

    error_message: Optional[str] = None

    def summary(self) -> str:
        """Return a human-readable multi-line summary."""
        lines = [
            "─" * 55,
            f"  Symbol       : {self.symbol}",
            f"  Side         : {self.side}",
            f"  Order Type   : {self.order_type}",
            f"  Quantity     : {self.quantity}",
        ]
        if self.price is not None:
            lines.append(f"  Price        : {self.price}")

        if self.success:
            lines += [
                "─" * 55,
                f"  Order ID     : {self.order_id}",
                f"  Client OID   : {self.client_order_id}",
                f"  Status       : {self.status}",
                f"  Executed Qty : {self.executed_qty}",
                f"  Avg Price    : {self.avg_price or 'N/A'}",
                "─" * 55,
                "  ✓  Order placed successfully.",
            ]
        else:
            lines += [
                "─" * 55,
                f"  ✗  Order FAILED: {self.error_message}",
            ]

        lines.append("─" * 55)
        return "\n".join(lines)


class OrderPlacer:
    """
    Orchestrates the full order lifecycle:
      1. Validate input parameters.
      2. Call the Binance client.
      3. Parse and return a structured OrderResult.

    Usage::

        placer = OrderPlacer(client)
        result = placer.place_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="LIMIT",
            quantity=0.001,
            price=30000.0,
        )
        print(result.summary())
    """

    def __init__(self, client: BinanceFuturesClient) -> None:
        self._client = client

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float | str,
        price: float | str | None = None,
    ) -> OrderResult:
        """
        Validate input and place a MARKET or LIMIT order.

        Returns an OrderResult regardless of success or failure —
        the caller can inspect `result.success` and `result.error_message`.
        """
        logger.info(
            "place_order called — symbol=%s side=%s type=%s qty=%s price=%s",
            symbol,
            side,
            order_type,
            quantity,
            price,
        )

        try:
            params = validate_order_params(symbol, side, order_type, quantity, price)
        except ValueError as exc:
            logger.warning("Validation failed: %s", exc)
            return OrderResult(
                success=False,
                symbol=str(symbol).upper(),
                side=str(side).upper(),
                order_type=str(order_type).upper(),
                quantity=float(quantity) if quantity else 0.0,
                price=float(price) if price else None,
                error_message=str(exc),
            )

        try:
            response = self._client.new_order(
                symbol=params["symbol"],
                side=params["side"],
                order_type=params["order_type"],
                quantity=params["quantity"],
                price=params["price"],
            )
        except BinanceAPIError as exc:
            logger.error("API error while placing order: %s", exc)
            return OrderResult(
                success=False,
                symbol=params["symbol"],
                side=params["side"],
                order_type=params["order_type"],
                quantity=params["quantity"],
                price=params["price"],
                error_message=str(exc),
            )
        except BinanceNetworkError as exc:
            logger.error("Network error while placing order: %s", exc)
            return OrderResult(
                success=False,
                symbol=params["symbol"],
                side=params["side"],
                order_type=params["order_type"],
                quantity=params["quantity"],
                price=params["price"],
                error_message=str(exc),
            )

        result = OrderResult(
            success=True,
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params["price"],
            order_id=response.get("orderId"),
            client_order_id=response.get("clientOrderId"),
            status=response.get("status"),
            executed_qty=response.get("executedQty"),
            avg_price=response.get("avgPrice"),
            raw_response=response,
        )

        logger.info(
            "Order placed — orderId=%s status=%s executedQty=%s avgPrice=%s",
            result.order_id,
            result.status,
            result.executed_qty,
            result.avg_price,
        )
        return result
