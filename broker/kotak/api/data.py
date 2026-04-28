import json
import time
import urllib.parse

import httpx
import pandas as pd

from database.token_db import get_br_symbol, get_brexchange, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


class BrokerData:
    def __init__(self, auth_token):
        parts = auth_token.split(":::")
        self.session_token = parts[0]
        self.session_sid = parts[1]
        self.base_url = parts[2]
        self.bearer_token = parts[3]
        self.server_id = parts[4] if len(parts) > 4 else ""

        if not self.base_url or not self.base_url.startswith("http"):
            raise ValueError(
                "Kotak auth token missing baseUrl. Please re-login (TOTP + MPIN) to refresh credentials."
            )

        self.base_url = self.base_url.rstrip("/")
        self.quotes_base_url = self.base_url
        self.last_quote_error = None
        logger.info(f"Using quotes baseUrl: {self.quotes_base_url}")

        self.timeframe_map = {}

    def _get_kotak_exchange(self, exchange):
        exchange_map = {
            "NSE": "nse_cm",
            "BSE": "bse_cm",
            "NFO": "nse_fo",
            "BFO": "bse_fo",
            "CDS": "cde_fo",
            "MCX": "mcx_fo",
            "NSE_INDEX": "nse_cm",
            "BSE_INDEX": "bse_cm",
        }
        return exchange_map.get(exchange)

    def _get_index_symbol(self, symbol):
        index_map = {
            "NIFTY": "Nifty 50",
            "NIFTY50": "Nifty 50",
            "BANKNIFTY": "Nifty Bank",
            "SENSEX": "SENSEX",
            "BANKEX": "BANKEX",
            "FINNIFTY": "Nifty Fin Service",
            "MIDCPNIFTY": "NIFTY MIDCAP 100",
        }
        return index_map.get(symbol.upper(), symbol)

    def _make_quotes_request(self, query, filter_name="all"):
        """Make HTTP request to Neo API v2 quotes endpoint."""
        client = get_httpx_client()

        encoded_query = urllib.parse.quote(query, safe="|,")
        endpoint = f"/script-details/1.0/quotes/neosymbol/{encoded_query}/{filter_name}"

        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Sid": self.session_sid,
            "Auth": self.session_token,
            "neo-fin-key": "neotradeapi",
            "Content-Type": "application/json",
        }

        url = f"{self.quotes_base_url}{endpoint}"

        try:
            logger.info(f"QUOTES API - Making request to: {url}")

            response = client.get(url, headers=headers)
            logger.info(f"QUOTES API - Response status: {response.status_code} for {url}")

            if response.status_code == 200:
                response_data = json.loads(response.text)

                # Kotak returns 200 with a fault object for invalid symbols
                if isinstance(response_data, dict) and "fault" in response_data:
                    self.last_quote_error = {
                        "status": 400,
                        "body": response_data["fault"].get("description", "Invalid symbol"),
                        "url": url,
                    }
                    logger.warning(f"QUOTES API - Fault response: {response_data['fault']}")
                    return None

                logger.debug(f"QUOTES API - Raw response: {response.text[:200]}...")
                self.last_quote_error = None
                return response_data

            self.last_quote_error = {"status": response.status_code, "body": response.text[:500], "url": url}
            logger.warning(f"QUOTES API - HTTP {response.status_code}: {response.text[:200]}...")

        except httpx.HTTPError as e:
            self.last_quote_error = {"error": str(e), "url": url}
            logger.error(f"HTTP error in _make_quotes_request ({url}): {e}")
        except Exception as e:
            self.last_quote_error = {"error": str(e), "url": url}
            logger.error(f"Error in _make_quotes_request ({url}): {e}")

        return None

    def get_quotes(self, symbol, exchange):
        try:
            logger.info(f"QUOTES API - Symbol: {symbol}, Exchange: {exchange}")

            if "INDEX" in exchange.upper():
                kotak_exchange = self._get_kotak_exchange(exchange)
                neo_symbol = self._get_index_symbol(symbol)
                query = f"{kotak_exchange}|{neo_symbol}"
                logger.info(f"QUOTES API - Index query: {symbol} -> {neo_symbol} -> {query}")
            else:
                psymbol = get_token(symbol, exchange)
                brexchange = get_brexchange(symbol, exchange)
                logger.info(f"QUOTES API - pSymbol: {psymbol}, brexchange: {brexchange}")

                if not psymbol or not brexchange:
                    logger.error(f"pSymbol or brexchange not found for {symbol} on {exchange}")
                    return self._get_default_quote()

                if brexchange in ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"]:
                    kotak_exchange = self._get_kotak_exchange(brexchange)
                else:
                    kotak_exchange = brexchange

                query = f"{kotak_exchange}|{psymbol}"
                logger.info(f"QUOTES API - Query: {query}")

            response = self._make_quotes_request(query, "all")

            if not response or not isinstance(response, list) or len(response) == 0:
                logger.error(
                    f"QUOTES API - Query failed for {symbol}; last_error={self.last_quote_error}"
                )
                return None

            quote_data = response[0]

            ohlc_data = quote_data.get("ohlc", {})
            ltp_parsed = float(quote_data.get("ltp", 0))

            depth_data = quote_data.get("depth", {})
            buy_orders = depth_data.get("buy", [])
            sell_orders = depth_data.get("sell", [])

            bid_price = float(buy_orders[0].get("price", 0)) if buy_orders else ltp_parsed
            ask_price = float(sell_orders[0].get("price", 0)) if sell_orders else ltp_parsed

            return {
                "bid": bid_price,
                "ask": ask_price,
                "open": float(ohlc_data.get("open", 0)),
                "high": float(ohlc_data.get("high", 0)),
                "low": float(ohlc_data.get("low", 0)),
                "ltp": ltp_parsed,
                "prev_close": float(ohlc_data.get("close", 0)),
                "volume": float(quote_data.get("last_volume", 0)),
                "oi": int(quote_data.get("open_int", 0)),
            }

        except Exception as e:
            logger.error(f"Error in get_quotes: {e}")
            return self._get_default_quote()

    def get_depth(self, symbol: str, exchange: str) -> dict:
        try:
            logger.info(f"DEPTH API - Symbol: {symbol}, Exchange: {exchange}")

            if "INDEX" in exchange.upper():
                kotak_exchange = self._get_kotak_exchange(exchange)
                neo_symbol = self._get_index_symbol(symbol)
                query = f"{kotak_exchange}|{neo_symbol}"
            else:
                psymbol = get_token(symbol, exchange)
                brexchange = get_brexchange(symbol, exchange)

                if not psymbol or brexchange is None:
                    logger.error(f"pSymbol or brexchange not found for {symbol} on {exchange}")
                    return self._get_default_depth()

                if brexchange in ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"]:
                    kotak_exchange = self._get_kotak_exchange(brexchange)
                else:
                    kotak_exchange = brexchange

                query = f"{kotak_exchange}|{psymbol}"

            response = self._make_quotes_request(query, "depth")

            if response and isinstance(response, list) and len(response) > 0:
                target_quote = response[0]
                depth_data = target_quote.get("depth", {})

                bids = []
                asks = []

                buy_data = depth_data.get("buy", [])
                if isinstance(buy_data, list):
                    for bid in buy_data[:5]:
                        bids.append({
                            "price": float(bid.get("price", 0)),
                            "quantity": int(bid.get("quantity", 0)),
                        })

                sell_data = depth_data.get("sell", [])
                if isinstance(sell_data, list):
                    for ask in sell_data[:5]:
                        asks.append({
                            "price": float(ask.get("price", 0)),
                            "quantity": int(ask.get("quantity", 0)),
                        })

                while len(bids) < 5:
                    bids.append({"price": 0, "quantity": 0})
                while len(asks) < 5:
                    asks.append({"price": 0, "quantity": 0})

                return {
                    "bids": bids,
                    "asks": asks,
                    "totalbuyqty": sum(b["quantity"] for b in bids if b["quantity"] > 0),
                    "totalsellqty": sum(a["quantity"] for a in asks if a["quantity"] > 0),
                }
            else:
                logger.warning(f"No depth data received for {symbol}")
                return self._get_default_depth()

        except Exception as e:
            logger.error(f"Error in get_depth: {e}")
            return self._get_default_depth()

    def get_multiquotes(self, symbols: list) -> list:
        try:
            BATCH_SIZE = 50
            RATE_LIMIT_DELAY = 0.2

            if len(symbols) > BATCH_SIZE:
                all_results = []
                for i in range(0, len(symbols), BATCH_SIZE):
                    batch = symbols[i : i + BATCH_SIZE]
                    batch_results = self._process_quotes_batch(batch)
                    all_results.extend(batch_results)
                    if i + BATCH_SIZE < len(symbols):
                        time.sleep(RATE_LIMIT_DELAY)
                return all_results
            else:
                return self._process_quotes_batch(symbols)

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")

    def _process_quotes_batch(self, symbols: list) -> list:
        queries = []
        query_map = {}
        skipped_symbols = []

        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            try:
                if "INDEX" in exchange.upper():
                    kotak_exchange = self._get_kotak_exchange(exchange)
                    neo_symbol = self._get_index_symbol(symbol)
                    query = f"{kotak_exchange}|{neo_symbol}"
                else:
                    psymbol = get_token(symbol, exchange)
                    brexchange = get_brexchange(symbol, exchange)

                    if not psymbol or not brexchange:
                        skipped_symbols.append({
                            "symbol": symbol, "exchange": exchange,
                            "error": "Could not resolve pSymbol or brexchange",
                        })
                        continue

                    if brexchange in ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"]:
                        kotak_exchange = self._get_kotak_exchange(brexchange)
                    else:
                        kotak_exchange = brexchange

                    query = f"{kotak_exchange}|{psymbol}"

                queries.append(query)
                query_map[query] = {"symbol": symbol, "exchange": exchange}

            except Exception as e:
                skipped_symbols.append({"symbol": symbol, "exchange": exchange, "error": str(e)})
                continue

        if not queries:
            return skipped_symbols

        combined_query = ",".join(queries)
        logger.info(f"Requesting quotes for {len(queries)} instruments")

        response_data = self._make_quotes_request(combined_query, "all")
        if response_data is None:
            logger.error(f"API Error: {self.last_quote_error}")
            raise Exception(f"API Error: {self.last_quote_error}")

        results = []

        if not response_data or not isinstance(response_data, list):
            return results

        response_lookup = {}
        for quote in response_data:
            exch = quote.get("exchange", "")
            token = quote.get("exchange_token", "")
            display = quote.get("display_symbol", "")

            key1 = f"{exch}|{token}"
            key2 = f"{exch}|{display.replace('-EQ', '').replace('-IN', '')}" if display else None

            response_lookup[key1] = quote
            if key2:
                response_lookup[key2] = quote

        for query, original in query_map.items():
            quote_data = response_lookup.get(query)

            if not quote_data:
                for resp_key, resp_quote in response_lookup.items():
                    if query.lower() == resp_key.lower():
                        quote_data = resp_quote
                        break

            if not quote_data:
                results.append({
                    "symbol": original["symbol"],
                    "exchange": original["exchange"],
                    "error": "No quote data available",
                })
                continue

            ohlc_data = quote_data.get("ohlc", {})
            depth_data = quote_data.get("depth") or {}
            buy_orders = depth_data.get("buy", [])
            sell_orders = depth_data.get("sell", [])

            ltp = float(quote_data.get("ltp", 0))
            bid_price = float(buy_orders[0].get("price", 0)) if buy_orders else ltp
            ask_price = float(sell_orders[0].get("price", 0)) if sell_orders else ltp

            results.append({
                "symbol": original["symbol"],
                "exchange": original["exchange"],
                "data": {
                    "bid": bid_price,
                    "ask": ask_price,
                    "open": float(ohlc_data.get("open", 0)),
                    "high": float(ohlc_data.get("high", 0)),
                    "low": float(ohlc_data.get("low", 0)),
                    "ltp": ltp,
                    "prev_close": float(ohlc_data.get("close", 0)),
                    "volume": float(quote_data.get("last_volume", 0)),
                    "oi": int(quote_data.get("open_int", 0)),
                },
            })

        return skipped_symbols + results

    def _get_default_quote(self):
        return {
            "bid": 0, "ask": 0, "open": 0, "high": 0, "low": 0,
            "ltp": 0, "prev_close": 0, "volume": 0, "oi": 0,
        }

    def _get_default_depth(self):
        return {
            "bids": [{"price": 0, "quantity": 0} for _ in range(5)],
            "asks": [{"price": 0, "quantity": 0} for _ in range(5)],
            "totalbuyqty": 0,
            "totalsellqty": 0,
        }

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        empty_df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        logger.warning("Kotak Neo does not support historical data")
        return empty_df

    def get_supported_intervals(self) -> dict:
        return {
            "seconds": [], "minutes": [], "hours": [],
            "days": [], "weeks": [], "months": [],
        }
