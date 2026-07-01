import math
import time
from abc import ABC
from typing import Any

import httpx

from config import BASE_PRICES, DEFAULT_SYMBOLS, FALLBACK_TOP_SYMBOLS


class BaseExchangeAdapter(ABC):
    name = "Base"
    supports_real_data = False
    cache_ttl_seconds = 20

    def __init__(self, timeout: float = 6.0) -> None:
        self.timeout = timeout
        self.last_error: str | None = None
        self.last_source: str = "fallback"
        self.last_ticker_status: str = "fallback"
        self.last_orderbook_status: str = "fallback"
        self.last_top_symbols: list[str] = []
        self.last_real_ticker_count = 0
        self.last_real_orderbook_count = 0
        self._cache: dict[str, tuple[float, Any]] = {}

    def _cache_get(self, key: str, ttl: int | None = None) -> Any | None:
        item = self._cache.get(key)
        if not item:
            return None
        timestamp, value = item
        if time.time() - timestamp > (ttl or self.cache_ttl_seconds):
            self._cache.pop(key, None)
            return None
        return value

    def _cache_set(self, key: str, value: Any) -> Any:
        self._cache[key] = (time.time(), value)
        return value

    def _format_error(self, label: str, error: Exception) -> str:
        if isinstance(error, httpx.HTTPStatusError):
            body = error.response.text[:500] if error.response is not None else ""
            return f"{label}: HTTP {error.response.status_code} {body}"
        return f"{label}: {type(error).__name__}: {error}"

    def _record_error(self, label: str, error: Exception) -> None:
        self.last_error = self._format_error(label, error)

    def _is_ssl_verify_error(self, error: Exception) -> bool:
        return "CERTIFICATE_VERIFY_FAILED" in str(error) or "Hostname mismatch" in str(error)

    async def _get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        label: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        errors: list[str] = []
        request_label = label or url
        request_headers = {
            "Accept": "application/json,text/plain,*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
        }
        if headers:
            request_headers.update(headers)
        for verify in (True, False):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    verify=verify,
                    follow_redirects=True,
                    headers=request_headers,
                ) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    try:
                        return response.json()
                    except ValueError as error:
                        snippet = response.text[:180].replace("\n", " ").replace("\r", " ")
                        raise RuntimeError(f"{request_label}: non-json response from exchange: {snippet}") from error
            except Exception as error:
                message = self._format_error(request_label, error)
                errors.append(message)
                self._record_error(request_label, error)
                if verify is True and self._is_ssl_verify_error(error):
                    continue
                if verify is True:
                    break
        raise RuntimeError("; ".join(errors))

    async def fetch_top_symbols(self, limit: int = 20) -> list[str]:
        self.last_top_symbols = FALLBACK_TOP_SYMBOLS[:limit]
        return self.last_top_symbols

    async def fetch_tickers(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        self.last_ticker_status = "fallback"
        self.last_real_ticker_count = 0
        return self.mock_tickers(symbols)

    async def fetch_orderbook(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        self.last_orderbook_status = "fallback"
        ticker = self.mock_tickers([symbol])[symbol]
        return self.mock_orderbook(symbol, ticker["lastPrice"], limit)

    async def fetch_derivatives(self, symbols: list[str]) -> dict[str, dict[str, float | None]]:
        return {symbol: {"fundingRate": None, "openInterest": None} for symbol in symbols}

    def debug_status(self, symbol_count: int | None = None) -> dict[str, Any]:
        count = symbol_count if symbol_count is not None else len(self.last_top_symbols)
        if self.last_ticker_status == "real" and self.last_orderbook_status == "real":
            source_status = "real"
        elif self.last_ticker_status == "fallback" and self.last_orderbook_status == "fallback":
            source_status = "fallback"
        else:
            source_status = "partial_real"
        return {
            "exchange": self.name,
            "sourceStatus": source_status,
            "tickerStatus": self.last_ticker_status,
            "orderbookStatus": self.last_orderbook_status,
            "symbolCount": count,
            "topSymbols": self.last_top_symbols[:count],
            "lastError": self.last_error,
        }

    def mock_tickers(self, symbols: list[str] | None = None) -> dict[str, dict[str, Any]]:
        selected = symbols or FALLBACK_TOP_SYMBOLS
        tick = int(time.time())
        result: dict[str, dict[str, Any]] = {}
        for index, symbol in enumerate(selected):
            base = BASE_PRICES.get(symbol, 100.0 + index * 7)
            wave = math.sin(tick / 37 + index * 0.77)
            drift = math.cos(tick / 83 + index) * 0.0018
            last_price = base * (1 + wave * 0.006 + drift)
            spread_pct = 0.006 + index * 0.0011 + abs(math.sin(tick / 59 + index)) * 0.004
            spread = last_price * spread_pct / 100
            best_bid = last_price - spread / 2
            best_ask = last_price + spread / 2
            volume_24h = (base * (85000 + index * 11000)) * (1 + abs(wave) * 0.25)
            result[symbol] = {
                "symbol": symbol,
                "lastPrice": last_price,
                "bestBid": best_bid,
                "bestAsk": best_ask,
                "bidQty": 10 + index * 3 + abs(wave) * 8,
                "askQty": 9 + index * 2 + abs(math.cos(tick / 41 + index)) * 8,
                "volume24h": volume_24h,
                "change24h": wave * 4.2,
                "fundingRate": 0.0001 * math.sin(index + tick / 300),
                "openInterest": volume_24h * (0.25 + index * 0.015),
            }
        return result

    def mock_orderbook(self, symbol: str, last_price: float, limit: int = 20) -> dict[str, Any]:
        tick = int(time.time())
        symbol_index = max(0, DEFAULT_SYMBOLS.index(symbol)) if symbol in DEFAULT_SYMBOLS else 0
        step = 0.00018 + symbol_index * 0.000025
        bids: list[list[float]] = []
        asks: list[list[float]] = []
        for level in range(limit):
            bid_price = last_price * (1 - step * (level + 1))
            ask_price = last_price * (1 + step * (level + 1))
            base_size = 42000 + symbol_index * 9000 + level * 5200
            bid_size_usdt = base_size * (1 + abs(math.sin(tick / 23 + level + symbol_index)))
            ask_size_usdt = base_size * (1 + abs(math.cos(tick / 29 + level + symbol_index)))

            if level in (3, 8) and symbol_index % 3 == 0:
                bid_size_usdt += 120000 + symbol_index * 22000
            if level in (5, 10) and symbol_index % 2 == 1:
                ask_size_usdt += 125000 + symbol_index * 18000

            bids.append([round(bid_price, 8), round(bid_size_usdt / bid_price, 8)])
            asks.append([round(ask_price, 8), round(ask_size_usdt / ask_price, 8)])
        return {"symbol": symbol, "bids": bids, "asks": asks}
