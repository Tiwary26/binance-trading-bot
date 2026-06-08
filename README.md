# Binance Futures Testnet Trading Bot

A clean, production-ready Python CLI application for placing orders on the
[Binance Futures Testnet](https://testnet.binancefuture.com) (USDT-M perpetual futures).

---

## Features

- Place **MARKET** and **LIMIT** orders (BUY / SELL)
- Clean layered architecture — API client, order logic, and CLI are fully separated
- Structured **logging** to a rotating file (`logs/trading_bot.log`) + console
- Strict **input validation** with descriptive error messages
- Graceful **exception handling** for API errors and network failures
- `--dry-run` flag to validate inputs without sending to the API
- Credentials via environment variables (recommended) or CLI flags

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package marker
│   ├── client.py            # Binance REST client (signing, requests, error handling)
│   ├── orders.py            # Order placement logic + OrderResult dataclass
│   ├── validators.py        # Input validation (symbol, side, type, qty, price)
│   └── logging_config.py    # Logging setup (file + console handlers)
├── cli.py                   # CLI entry point (argparse)
├── logs/
│   ├── market_order.log     # Sample log — MARKET order
│   └── limit_order.log      # Sample log — LIMIT order
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Prerequisites

- Python 3.9 or higher
- A [Binance Futures Testnet](https://testnet.binancefuture.com) account with API credentials

### 2. Clone / Download

```bash
git clone https://github.com/<your-username>/trading-bot.git
cd trading-bot/trading_bot
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Credentials

**Option A — Environment variables (recommended):**

```bash
export BINANCE_API_KEY=your_testnet_api_key
export BINANCE_API_SECRET=your_testnet_api_secret
```

Or create a `.env` file in the `trading_bot/` directory:

```env
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
```

Then load it before running:

```bash
export $(cat .env | xargs)
```

**Option B — CLI flags (not recommended in shared environments):**

```bash
python cli.py --api-key <key> --api-secret <secret> ...
```

---

## How to Run

All commands are run from inside the `trading_bot/` directory.

### Place a MARKET BUY order

```bash
python cli.py \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.001
```

### Place a LIMIT SELL order

```bash
python cli.py \
  --symbol BTCUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.001 \
  --price 105000.00
```

### Place a MARKET SELL on ETHUSDT

```bash
python cli.py \
  --symbol ETHUSDT \
  --side SELL \
  --type MARKET \
  --quantity 0.01
```

### Validate inputs without sending (dry run)

```bash
python cli.py \
  --symbol BTCUSDT \
  --side BUY \
  --type LIMIT \
  --quantity 0.001 \
  --price 95000 \
  --dry-run
```

### Increase console verbosity (see raw API traffic)

```bash
python cli.py \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.001 \
  --log-level DEBUG
```

---

## Sample Output

```
=======================================================
  ORDER REQUEST SUMMARY
=======================================================
  Symbol       : BTCUSDT
  Side         : BUY
  Order Type   : MARKET
  Quantity     : 0.001
=======================================================

  ORDER RESPONSE
-------------------------------------------------------
  Symbol       : BTCUSDT
  Side         : BUY
  Order Type   : MARKET
  Quantity     : 0.001
-------------------------------------------------------
  Order ID     : 3942158721
  Client OID   : abc123xyz
  Status       : FILLED
  Executed Qty : 0.001
  Avg Price    : 104823.50
-------------------------------------------------------
  ✓  Order placed successfully.
-------------------------------------------------------
```

---

## CLI Reference

| Flag | Required | Description |
|------|----------|-------------|
| `--symbol` | Yes | Trading pair, e.g. `BTCUSDT`, `ETHUSDT` |
| `--side` | Yes | `BUY` or `SELL` |
| `--type` | Yes | `MARKET` or `LIMIT` |
| `--quantity` | Yes | Order size in base asset (e.g. `0.001` BTC) |
| `--price` | LIMIT only | Limit price in USDT |
| `--api-key` | If not in env | Binance Testnet API key |
| `--api-secret` | If not in env | Binance Testnet API secret |
| `--log-level` | No | Console verbosity: `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `--dry-run` | No | Validate inputs only, skip API call |

---

## Logging

- **File**: `logs/trading_bot.log` — rotates at 5 MB, keeps 3 backups, logs at `DEBUG` level.
- **Console**: logs at `INFO` level by default (change with `--log-level`).

Log format:

```
2025-06-08T14:23:01 | INFO     | trading_bot.orders | Placing BUY MARKET order — symbol=BTCUSDT qty=0.001 price=None
2025-06-08T14:23:02 | INFO     | trading_bot.orders | Order placed — orderId=3942158721 status=FILLED executedQty=0.001 avgPrice=104823.50
```

---

## Assumptions

1. **USDT-M perpetuals only.** The bot validates that every symbol ends with `USDT`.
2. **Testnet only.** The base URL is hardcoded to `https://testnet.binancefuture.com`.
   To switch to mainnet, change `BASE_URL` in `bot/client.py` (**do this at your own risk**).
3. **No position-side awareness.** Orders are sent in one-way (single direction) mode.
   If your testnet account is in hedge mode, add `positionSide=BOTH` to the request params in `client.py`.
4. **LIMIT orders default to `timeInForce=GTC`** (Good Till Cancelled).
5. Credentials are never logged.

---

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Missing credentials | Clear error message, exit code 1 |
| Invalid symbol / side / type | Descriptive validation error, exit code 1 |
| Missing price for LIMIT | Validation error, exit code 1 |
| Binance API error (e.g. -2010) | Error code + message printed, logged, exit code 1 |
| Network timeout / unreachable | User-friendly message, logged, exit code 1 |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP requests to Binance REST API |
| `python-dotenv` | Optional `.env` file support |

---

## License

MIT
