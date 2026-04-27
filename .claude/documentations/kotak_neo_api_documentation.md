# Kotak Neo API — Client Documentation

> **Official Python SDK for Kotak Neo Trade APIs**
> Sources: [kotak-neo-api (v1)](https://github.com/Kotak-Neo/kotak-neo-api) · [Kotak-neo-api-v2](https://github.com/Kotak-Neo/Kotak-neo-api-v2)

---

## Table of Contents

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Authentication](#authentication)
   - [v1 — OTP-based Login](#v1--otp-based-login)
   - [v2 — TOTP-based Login](#v2--totp-based-login)
5. [WebSocket Callbacks](#websocket-callbacks)
6. [Order Management](#order-management)
   - [Place Order](#place-order)
   - [Modify Order](#modify-order)
   - [Cancel Order](#cancel-order)
   - [Cancel Cover Order](#cancel-cover-order)
   - [Cancel Bracket Order](#cancel-bracket-order)
7. [Reports](#reports)
   - [Order Book](#order-book)
   - [Order History](#order-history)
   - [Trade Book](#trade-book)
8. [Portfolio](#portfolio)
   - [Positions](#positions)
   - [Holdings](#holdings)
9. [Funds & Margins](#funds--margins)
   - [Limits](#limits)
   - [Margin Required](#margin-required)
10. [Market Data](#market-data)
    - [Scrip Master](#scrip-master)
    - [Search Scrip](#search-scrip)
    - [Quotes](#quotes)
11. [WebSocket Streaming](#websocket-streaming)
    - [Live Feed (Subscribe)](#live-feed-subscribe)
    - [Unsubscribe](#unsubscribe)
    - [Order Feed](#order-feed)
12. [Session Management](#session-management)
13. [API Endpoint Reference](#api-endpoint-reference)
14. [Parameter Reference](#parameter-reference)

---

## Overview

The Kotak Neo Python SDK provides programmatic access to Kotak Neo's trading platform. It supports:

- **Authentication** via OTP (v1) or TOTP (v2)
- **Order management** — place, modify, cancel orders across equity and F&O segments
- **Market data** — live quotes, scrip master, and instrument search
- **Portfolio** — positions, holdings, limits, and margin calculation
- **Real-time streaming** — WebSocket live price feed and order feed

The platform supports **zero brokerage** on API orders and processes over **1 million trades per day** at ultra-low latency. SDKs are compatible with Python and the REST APIs are language-agnostic (works with Java, C#, Node.js, Go, etc.).

---

## Requirements

| SDK Version | Python Version |
|---|---|
| v1 (kotak-neo-api) | Python 2.7+ and 3.0+ |
| v2 (Kotak-neo-api-v2) | Python 3.10 to 3.13 |

---

## Installation

### SDK v2 (Latest — Recommended)

**Install via pip (GitHub):**

```bash
pip install "git+https://github.com/Kotak-Neo/Kotak-neo-api-v2.git@v2.0.1#egg=neo_api_client"
```

**Force reinstall / upgrade:**

```bash
pip install --force-reinstall "git+https://github.com/Kotak-Neo/Kotak-neo-api-v2.git@v2.0.1#egg=neo_api_client"
```

> To switch versions, replace `@v2.0.1` with the desired tag, e.g. `@v2.0.0`.

**Install via Setuptools:**

```bash
python setup.py install --user
# or for all users:
sudo python setup.py install
```

**Import:**

```python
import neo_api_client
```

---

### SDK v1 (Legacy)

**Install via pip (GitHub):**

```bash
pip install "git+https://github.com/Kotak-Neo/kotak-neo-api.git#egg=neo_api_client"
```

**Force reinstall / upgrade:**

```bash
pip install --force-reinstall "git+https://github.com/Kotak-Neo/kotak-neo-api"
```

**Import:**

```python
import neo_api_client
```

---

## Authentication

### v2 — TOTP-based Login

SDK v2 uses a **consumer key** (token from your NEO app) and **TOTP** (Time-based One-Time Password) for secure, two-step authentication.

#### Step 1: Register for TOTP (One-time Setup)

1. Visit [https://www.kotaksecurities.com/platform/kotak-neo-trade-api/](https://www.kotaksecurities.com/platform/kotak-neo-trade-api/) and select **Register for TOTP**.
2. Verify your mobile number with OTP.
3. Select the account for TOTP registration.
4. Select the option to register for TOTP.
5. Scan the QR code (valid for 5 minutes) using any authenticator app (Google Authenticator, Microsoft Authenticator, etc.).
6. You will start receiving TOTPs on the authenticator app.
7. Submit the TOTP on the QR code page to complete registration.

#### Step 2: Get Your Consumer Key

1. Log in to the Kotak NEO app or web portal.
2. Navigate to **Invest → Trade API → API Dashboard**.
3. Click **"Create Application"** and securely save your generated token.
4. This token is your `consumer_key`.

#### Step 3: Initialise Client

```python
from neo_api_client import NeoAPI

# consumer_key: Token from NEO app/web (Invest > Trade API)
# environment: Pass 'prod' for live server
# access_token: Optional — pass None unless you have a barrier token
# neo_fin_key: Optional — pass None

client = NeoAPI(
    environment='prod',
    access_token=None,
    neo_fin_key=None,
    consumer_key='YOUR_TOKEN'
)
```

#### Step 4: TOTP Login

```python
# mobile_number: Registered mobile number with country code (e.g. +919999999999)
# ucc: Unique Client Code — found in profile section of app/web
# totp: 6-digit TOTP from your authenticator app
# Returns: view_token and session_id used to generate trade token

client.totp_login(mobile_number="+919999999999", ucc="YOUR_UCC", totp='123456')
```

#### Step 5: TOTP Validation (Generate Trade Token)

```python
# mpin: Your 6-digit NEO account MPIN
# Returns: trade_token used for all subsequent API calls

client.totp_validate(mpin="YOUR_MPIN")
```

---

### v1 — OTP-based Login

SDK v1 uses `consumer_key`, `consumer_secret`, and a mobile OTP for authentication.

#### Step 1: Initialise Client

```python
from neo_api_client import NeoAPI

def on_message(message):
    print(message)

def on_error(error_message):
    print(error_message)

def on_close(message):
    print(message)

def on_open(message):
    print(message)

# consumer_key, consumer_secret: API credentials from Kotak NEO
# environment: 'uat' (default) or 'prod' for live server
# access_token: Optional barrier token — if provided, consumer_key/secret are optional
# neo_fin_key: Optional

client = NeoAPI(
    consumer_key="YOUR_CONSUMER_KEY",
    consumer_secret="YOUR_CONSUMER_SECRET",
    environment='uat',
    access_token=None,
    neo_fin_key=None
)
```

#### Step 2: Login (Generate OTP)

```python
# Accepts: mobilenumber & password, OR pan & password, OR userid & password
# This call also triggers OTP generation for 2FA

client.login(mobilenumber="+919999999999", password="YOUR_PASSWORD")
```

#### Step 3: Complete 2FA (Session Token)

```python
# OTP received via SMS on your registered mobile number

client.session_2fa(OTP="123456")
```

---

## WebSocket Callbacks

Set up optional callbacks before using the WebSocket streaming features. These apply to both SDK v1 and v2.

```python
def on_message(message):
    """Called when a message is received from the WebSocket."""
    print(message)

def on_error(error_message):
    """Called when any error or exception occurs in code or WebSocket."""
    print(error_message)

def on_close(message):
    """Called when the WebSocket connection is closed."""
    print(message)

def on_open(message):
    """Called when the WebSocket successfully connects."""
    print(message)

# Attach callbacks to client
client.on_message = on_message
client.on_error = on_error
client.on_close = on_close
client.on_open = on_open
```

---

## Order Management

### Place Order

```python
client.place_order(
    exchange_segment="",        # See exchange_segment values below
    product="",                 # NRML, CNC, MIS, CO, BO, MTF
    price="",                   # Scrip price
    order_type="",              # L, MKT, SL, SL-M
    quantity="",                # Stock quantity (use lot size, not number of lots)
    validity="",                # DAY, IOC, GTC, EOS, GTD
    trading_symbol="",          # From scrip master file
    transaction_type="",        # B (Buy) or S (Sell)
    amo="NO",                   # After Market Order: YES or NO
    disclosed_quantity="0",     # Portion visible in market depth (0 to quantity)
    market_protection="0",      # Market Price Protection % (e.g. 5 = ±5% of LTP)
    pf="N",                     # Default: N
    trigger_price="0",          # Price at which SL/SL-M order is triggered
    tag=None,                   # Optional custom tag to track order

    # Bracket Order parameters (applicable only for BO)
    scrip_token=None,
    square_off_type=None,       # 'Absolute' or 'Ticks'
    stop_loss_type=None,        # 'Absolute' or 'Ticks'
    stop_loss_value=None,
    square_off_value=None,
    last_traded_price=None,
    trailing_stop_loss=None,    # 'Y' or 'N'
    trailing_sl_value=None,     # 'Y' or 'N'
)
```

**Exchange Segment & Supported Products/Order Types:**

| `exchange_segment` | Supported `product` | Supported `order_type` |
|---|---|---|
| `nse_cm` | NRML, CNC, MIS, CO, BO | L, MKT, SL, SL-M |
| `bse_cm` | NRML, CNC, MIS, CO, BO | L, MKT, SL, SL-M |
| `nse_fo` | NRML, MIS, BO | L, MKT, SL, SL-M |
| `bse_fo` | NRML, MIS | L, MKT, SL, SL-M |
| `mcx_fo` | NRML, MIS | L, MKT, SL, SL-M |
| `cde_fo` | NRML, MIS | L, MKT, SL, SL-M |

> **Note on quantity:** If one lot size is 25, pass `quantity="25"` (not `quantity="1"`). The same applies to `disclosed_quantity`.

> **Note on `disclosed_quantity`:** Disclosed Quantity (DQ) allows traders to show only a portion of their order to the market. For example, if quantity is 10, disclosed_quantity can be 0–10.

> **Note on `market_protection`:** Market Price Protection (MPP) protects against sudden price movements. E.g., if LTP is ₹100 and protection is 5%, a buy order is placed as a limit at ₹105 — only executes if sellers are available at or below ₹105.

---

### Modify Order

```python
# order_id: Order ID received from place_order response
client.modify_order(
    order_id="",
    price="7.0",
    quantity="2",
    disclosed_quantity="0",
    trigger_price="0",
    validity="DAY",             # DAY, IOC, GTC, EOS, GTD
    order_type=''               # L, MKT, SL, SL-M
)
```

---

### Cancel Order

**Simple cancel:**

```python
# order_id: Order ID received from place_order response
client.cancel_order(order_id="")
```

**Cancel with status verification:**

```python
# isVerify=True: First checks order status.
# If status is NOT 'rejected', 'cancelled', 'traded', or 'completed' — proceeds to cancel.
# If status IS one of the above — displays status to user instead.
# amo: After Market Order flag — YES or NO

client.cancel_order(order_id="", amo="", isVerify=True)
```

---

### Cancel Cover Order

```python
# Simple cancel
client.cancel_cover_order(order_id="")

# With status verification
client.cancel_cover_order(order_id="", amo="", isVerify=False)
```

---

### Cancel Bracket Order

```python
# Simple cancel
client.cancel_bracket_order(order_id="")

# With status verification
client.cancel_bracket_order(order_id="", amo="", isVerify=False)
```

---

## Reports

### Order Book

Retrieves the complete list of orders in the order book.

```python
client.order_report()
```

---

### Order History

Retrieves the full order history for a specific order ID.

```python
# order_id: Order ID received from place_order response
client.order_history(order_id="")
```

---

### Trade Book

Retrieves a list of all executed trades.

```python
# All trades
client.trade_report()

# Trades for a specific order
client.trade_report(order_id="")
```

---

## Portfolio

### Positions

Retrieves all current open positions.

```python
client.positions()
```

---

### Holdings

Retrieves the current portfolio holdings.

```python
client.holdings()
```

---

## Funds & Margins

### Limits

Retrieves available funds/limits for the given segment, exchange, and product.

```python
# segment: CASH, CUR, FO, ALL (default: ALL)
# exchange: ALL, NSE, BSE
# product: NRML, CNC, MIS, ALL

client.limits(segment="", exchange="", product="")
```

---

### Margin Required

Calculates the margin required for a given trade before placing an order.

```python
# exchange_segment: nse_cm, bse_cm, nse_fo, bse_fo, cde_fo, mcx_fo
# price: Scrip price
# order_type: L, MKT, SL, SL-M
# product: NRML, CNC, MIS, CO, BO
# quantity: Stock quantity
# instrument_token: Instrument token from scrip master
# transaction_type: B (Buy) or S (Sell)

client.margin_required(
    exchange_segment="",
    price="",
    order_type="",
    product="",
    quantity="",
    instrument_token="",
    transaction_type=""
)
```

---

## Market Data

### Scrip Master

Downloads the complete list of tradeable instruments as a CSV file.

```python
# All exchange segments
client.scrip_master()

# Specific exchange segment
# exchange_segment: nse_cm, bse_cm, nse_fo, bse_fo, cde_fo, mcx_fo
client.scrip_master(exchange_segment="nse_cm")
```

---

### Search Scrip

Searches the scrip master for matching instruments.

```python
# exchange_segment: Mandatory. Values: nse_cm, bse_cm, nse_fo, bse_fo, cde_fo, mcx_fo
# symbol, expiry, option_type, strike_price: Optional filters

client.search_scrip(
    exchange_segment="nse_fo",
    symbol="NIFTY",
    expiry="27-Feb-2025",
    option_type="CE",
    strike_price="22000"
)
```

---

### Quotes

Fetches live quote data for one or more instruments.

**v2:**

```python
instrument_tokens = [
    {"instrument_token": "TOKEN1", "exchange_segment": "nse_cm"},
    {"instrument_token": "TOKEN2", "exchange_segment": "nse_fo"},
    {"instrument_token": "TOKEN3", "exchange_segment": "bse_cm"},
]

# quote_type values:
#   all           — Complete data (default)
#   depth         — Market depth
#   ohlc          — Open, High, Low, Close
#   ltp           — Last Traded Price
#   oi            — Open Interest
#   52w           — 52-week high/low
#   circuit_limits — Circuit limits
#   scrip_details — Scrip details
#
# Note: Quotes API can be accessed with access_token alone (no full login required)

client.quotes(instrument_tokens=instrument_tokens, quote_type="all")
```

**v1 (additional parameters):**

```python
# v1 also supports direct token-based access without full login:
client.quotes(
    instrument_tokens=instrument_tokens,
    quote_type="ltp",           # market_depth, ohlc, ltp, 52w, circuit_limits, scrip_details
    isIndex=False,
    session_token="",
    sid="",
    server_id=""
)
```

---

## WebSocket Streaming

### Live Feed (Subscribe)

Subscribes to live price feed for the given instrument tokens.

```python
instrument_tokens = [
    {"instrument_token": "TOKEN1", "exchange_segment": "nse_cm"},
    {"instrument_token": "TOKEN2", "exchange_segment": "nse_fo"},
]

# isIndex: Set True to subscribe to index data (default: False)
# isDepth: Set True to receive market depth data (default: False)

client.subscribe(
    instrument_tokens=instrument_tokens,
    isIndex=False,
    isDepth=False
)
```

---

### Unsubscribe

Unsubscribes from live feed for given tokens. If a token is not currently subscribed, an error message is returned.

```python
client.un_subscribe(
    instrument_tokens=instrument_tokens,
    isIndex=False,
    isDepth=False
)
```

---

### Order Feed

Subscribes to real-time order status updates.

```python
client.subscribe_to_orderfeed()
```

> **Note:** Order feed includes a heartbeat mechanism (v1.2+) for a robust, persistent connection.

---

## Session Management

### Logout

Terminates the current user session.

```python
client.logout()
```

---

## API Endpoint Reference

### SDK v2 Endpoints

| Category | Method | Description |
|---|---|---|
| Session | `neo_api_client.SessionINIT` | Initialise Session |
| Authentication | `neo_api_client.Totp_login` | TOTP Login |
| Authentication | `neo_api_client.Totp_validation` | TOTP Validation (generate trade token) |
| Orders | `neo_api_client.placeorder` | Place Order |
| Orders | `neo_api_client.modifyorder` | Modify Order |
| Orders | `neo_api_client.cancelorder` | Cancel Order |
| Orders | `neo_api_client.cancelcoverorder` | Cancel Cover Order |
| Orders | `neo_api_client.cancelbracketorder` | Cancel Bracket Order |
| Reports | `neo_api_client.orderreport` | Order Book |
| Reports | `neo_api_client.orderhistory` | Order History |
| Reports | `neo_api_client.tradereport` | Trade Report |
| Portfolio | `neo_api_client.positions` | Positions |
| Portfolio | `neo_api_client.holdings` | Holdings |
| Funds | `neo_api_client.limits` | Limits |
| Funds | `neo_api_client.margin_required` | Margin Required |
| Market Data | `neo_api_client.scrip_master` | Scrip Master |
| Market Data | `neo_api_client.scrip_search` | Scrip Search |
| Market Data | `neo_api_client.quotes` | Quotes |
| Streaming | `neo_api_client.subscribe` | Subscribe Live Feed |
| Streaming | `neo_api_client.subscribeorderfeed` | Subscribe Order Feed |

---

### SDK v1 Endpoints

| Category | Method | Description |
|---|---|---|
| Session | `neo_api_client.SessionINIT` | Initialise Session |
| Authentication | `neo_api_client.NeoAPI` | Login NeoAPI |
| Authentication | `neo_api_client.2FA` | Session 2FA (OTP) |
| Orders | `neo_api_client.placeorder` | Place Order |
| Orders | `neo_api_client.modifyorder` | Modify Order |
| Orders | `neo_api_client.cancelorder` | Cancel Order |
| Reports | `neo_api_client.orderreport` | Order Report |
| Reports | `neo_api_client.tradereport` | Trade Report |
| Portfolio | `neo_api_client.positions` | Positions |
| Portfolio | `neo_api_client.holdings` | Holdings |
| Funds | `neo_api_client.limits` | Limits |
| Funds | `neo_api_client.margin_required` | Margin Required |
| Market Data | `neo_api_client.scrip_master` | Scrip Master |
| Market Data | `neo_api_client.scrip_search` | Scrip Search |
| Market Data | `neo_api_client.quotes` | Quotes |
| Streaming | `neo_api_client.subscribe` | Subscribe Live Feed |

---

## Parameter Reference

### Exchange Segments

| Value | Description |
|---|---|
| `nse_cm` | NSE Cash / Equity |
| `bse_cm` | BSE Cash / Equity |
| `nse_fo` | NSE Futures & Options |
| `bse_fo` | BSE Futures & Options |
| `cde_fo` | Currency Derivatives |
| `mcx_fo` | MCX Commodity Futures |

### Product Types

| Value | Description |
|---|---|
| `NRML` | Normal (carry forward) |
| `CNC` | Cash and Carry (delivery equity) |
| `MIS` | Margin Intraday Squareoff |
| `CO` | Cover Order |
| `BO` | Bracket Order |
| `MTF` | Margin Trade Financing |

### Order Types

| Value | Description |
|---|---|
| `L` | Limit Order |
| `MKT` | Market Order |
| `SL` | Stop-Loss Limit Order |
| `SL-M` | Stop-Loss Market Order |

### Validity Types

| Value | Description |
|---|---|
| `DAY` | Valid for the day |
| `IOC` | Immediate or Cancel |
| `GTC` | Good Till Cancelled |
| `EOS` | End of Session |
| `GTD` | Good Till Date |

### Transaction Types

| Value | Description |
|---|---|
| `B` | Buy |
| `S` | Sell |

### Quote Types (v2)

| Value | Description |
|---|---|
| `all` | Complete data (default) |
| `depth` | Market depth |
| `ohlc` | Open, High, Low, Close |
| `ltp` | Last Traded Price |
| `oi` | Open Interest |
| `52w` | 52-week high/low |
| `circuit_limits` | Circuit limits |
| `scrip_details` | Scrip details |

### Quote Types (v1)

| Value | Description |
|---|---|
| *(None)* | Complete data (default) |
| `market_depth` | Market depth |
| `ohlc` | Open, High, Low, Close |
| `ltp` | Last Traded Price |
| `52w` | 52-week high/low |
| `circuit_limits` | Circuit limits |
| `scrip_details` | Scrip details |

### Limit Segments

| Value | Description |
|---|---|
| `CASH` | Cash / Equity segment |
| `CUR` | Currency segment |
| `FO` | Futures & Options segment |
| `ALL` | All segments (default) |

---

## Complete Example — SDK v2

```python
from neo_api_client import NeoAPI

# ── WebSocket callbacks ──────────────────────────────────────────────────────
def on_message(message):
    print("Message:", message)

def on_error(error_message):
    print("Error:", error_message)

def on_close(message):
    print("Closed:", message)

def on_open(message):
    print("Connected:", message)

# ── Initialise client ────────────────────────────────────────────────────────
client = NeoAPI(
    environment='prod',
    access_token=None,
    neo_fin_key=None,
    consumer_key='YOUR_CONSUMER_KEY'
)

# ── Authenticate ─────────────────────────────────────────────────────────────
client.totp_login(mobile_number="+919999999999", ucc="YOUR_UCC", totp='123456')
client.totp_validate(mpin="YOUR_MPIN")

# ── Attach WebSocket callbacks ───────────────────────────────────────────────
client.on_message = on_message
client.on_error   = on_error
client.on_close   = on_close
client.on_open    = on_open

# ── Place an order ───────────────────────────────────────────────────────────
client.place_order(
    exchange_segment="nse_cm",
    product="CNC",
    price="500",
    order_type="L",
    quantity="1",
    validity="DAY",
    trading_symbol="INFY-EQ",
    transaction_type="B",
    amo="NO",
    disclosed_quantity="0",
    market_protection="0",
    pf="N",
    trigger_price="0",
    tag="my_order_tag"
)

# ── Query reports ────────────────────────────────────────────────────────────
client.order_report()
client.trade_report()
client.positions()
client.holdings()

# ── Market data ──────────────────────────────────────────────────────────────
client.scrip_master(exchange_segment="nse_cm")
client.search_scrip(exchange_segment="nse_fo", symbol="NIFTY")

instrument_tokens = [
    {"instrument_token": "11536", "exchange_segment": "nse_cm"},
]
client.quotes(instrument_tokens=instrument_tokens, quote_type="ltp")

# ── Live WebSocket streaming ──────────────────────────────────────────────────
client.subscribe(instrument_tokens=instrument_tokens, isIndex=False, isDepth=False)
client.subscribe_to_orderfeed()

# ── Logout ───────────────────────────────────────────────────────────────────
client.logout()
```

---

## Complete Example — SDK v1

```python
from neo_api_client import NeoAPI

def on_message(message):
    print(message)

def on_error(error_message):
    print(error_message)

def on_close(message):
    print(message)

def on_open(message):
    print(message)

# Initialise
client = NeoAPI(
    consumer_key="YOUR_CONSUMER_KEY",
    consumer_secret="YOUR_CONSUMER_SECRET",
    environment='prod',
    access_token=None,
    neo_fin_key=None
)

# Login
client.login(mobilenumber="+919999999999", password="YOUR_PASSWORD")
client.session_2fa(OTP="123456")

# Attach callbacks
client.on_message = on_message
client.on_error   = on_error
client.on_close   = on_close
client.on_open    = on_open

# Place order
client.place_order(
    exchange_segment='nse_cm',
    product='CNC',
    price='500',
    order_type='L',
    quantity=1,
    validity='DAY',
    trading_symbol='INFY-EQ',
    transaction_type='B',
    amo="NO",
    disclosed_quantity="0",
    market_protection="0",
    pf="N",
    trigger_price="0",
    tag=None
)

# Reports & portfolio
client.order_report()
client.order_history(order_id="YOUR_ORDER_ID")
client.trade_report()
client.positions()
client.holdings()
client.limits(segment="ALL", exchange="NSE", product="CNC")
client.margin_required(
    exchange_segment="nse_cm",
    price="500",
    order_type="L",
    product="CNC",
    quantity="1",
    instrument_token="11536",
    transaction_type="B"
)

# Market data
instrument_tokens = [
    {"instrument_token": "11536", "exchange_segment": "nse_cm"}
]
client.quotes(instrument_tokens=instrument_tokens, quote_type="ltp", isIndex=False)

# Subscribe
client.subscribe(instrument_tokens=instrument_tokens, isIndex=False, isDepth=False)
client.un_subscribe(instrument_tokens=instrument_tokens, isIndex=False, isDepth=False)
client.subscribe_to_orderfeed()

# Logout
client.logout()
```

---

## Additional Resources

- **Official GitHub — v2 SDK:** https://github.com/Kotak-Neo/Kotak-neo-api-v2
- **Official GitHub — v1 SDK:** https://github.com/Kotak-Neo/kotak-neo-api
- **Kotak Neo Trade API Platform:** https://www.kotakneo.com/platform/kotak-neo-trade-api/
- **TOTP Registration:** https://www.kotaksecurities.com/platform/kotak-neo-trade-api/
- **API Support:** https://www.kotakneo.com/support/trading/trade-api-and-terminals/

---

*Documentation compiled from official Kotak Neo GitHub repositories (v1.2 & v2.0.1). For the most up-to-date information, always refer to the official repositories.*
