"""
client.py
~~~~~~~~~
Low-level Binance Futures Testnet REST client.

Handles:
  - HMAC-SHA256 request signing.
  - X-MBX-APIKEY header injection.
  - Timestamp generation & recvWindow.
  - HTTP error surfacing with parsed Binance error codes.
  - Request / response logging at DEBUG level.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .logging_config import get_logger

logger = get_logger("client")

BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 10_000


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx response or an error payload."""

    def __init__(self, status_code: int, code: int, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"BinanceAPIError [{status_code}] code={code}: {message}")


class BinanceNetworkError(Exception):
    """Raised on connection/timeout failures."""


class BinanceFuturesClient:
    """
    Authenticated REST client for Binance Futures Testnet (USDT-M).

    Usage::

        client = BinanceFuturesClient(api_key="...", api_secret="...")
        response = client.new_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=0.001,
        )
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = BASE_URL,
        timeout: int = 15,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.info("BinanceFuturesClient initialised. Base URL: %s", self._base_url)

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add timestamp, recvWindow, and HMAC-SHA256 signature to params."""
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = RECV_WINDOW
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request.

        Args:
            method:   HTTP verb (GET / POST / DELETE).
            endpoint: API path, e.g. '/fapi/v1/order'.
            params:   Query / body parameters.
            signed:   Whether to add timestamp + signature.

        Returns:
            Parsed JSON response body.

        Raises:
            BinanceAPIError:     Non-2xx or Binance error payload.
            BinanceNetworkError: Connection / timeout failure.
        """
        params = params or {}
        if signed:
            params = self._sign(params)

        url = f"{self._base_url}{endpoint}"
        logger.debug(">>> %s %s | params: %s", method.upper(), url, params)

        try:
            if method.upper() in ("GET", "DELETE"):
                response = self._session.request(
                    method, url, params=params, timeout=self._timeout
                )
            else:
                response = self._session.request(
                    method, url, data=params, timeout=self._timeout
                )
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out: %s %s — %s", method, url, exc)
            raise BinanceNetworkError(
                f"Request to {url} timed out after {self._timeout}s."
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error: %s %s — %s", method, url, exc)
            raise BinanceNetworkError(
                f"Could not connect to {url}. Check network connectivity."
            ) from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Unexpected request error: %s", exc)
            raise BinanceNetworkError(f"Request failed: {exc}") from exc

        logger.debug(
            "<<< HTTP %s | body: %s", response.status_code, response.text[:500]
        )

        try:
            data = response.json()
        except ValueError:
            logger.error(
                "Non-JSON response (HTTP %s): %s",
                response.status_code,
                response.text[:200],
            )
            response.raise_for_status()
            raise BinanceAPIError(response.status_code, -1, response.text)

        if not response.ok or isinstance(data, dict) and "code" in data and data["code"] < 0:
            code = data.get("code", response.status_code)
            msg = data.get("msg", response.reason or "Unknown error")
            logger.error("Binance API error — code=%s message=%s", code, msg)
            raise BinanceAPIError(response.status_code, code, msg)

        return data

    def new_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """
        Place a new futures order.

        Args:
            symbol:        Trading pair, e.g. 'BTCUSDT'.
            side:          'BUY' or 'SELL'.
            order_type:    'MARKET' or 'LIMIT'.
            quantity:      Order quantity in base asset.
            price:         Limit price (required for LIMIT orders).
            time_in_force: GTC / IOC / FOK (LIMIT only).

        Returns:
            Full Binance order response dict.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("price is required for LIMIT orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force

        logger.info(
            "Placing %s %s order — symbol=%s qty=%s price=%s",
            side,
            order_type,
            symbol,
            quantity,
            price,
        )
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def get_exchange_info(self) -> Dict[str, Any]:
        """Retrieve exchange trading rules and symbol information (unsigned)."""
        return self._request("GET", "/fapi/v1/exchangeInfo", signed=False)

    def get_account(self) -> Dict[str, Any]:
        """Retrieve account information (balance, positions)."""
        return self._request("GET", "/fapi/v2/account", signed=True)
