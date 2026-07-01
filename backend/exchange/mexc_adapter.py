from typing import Any

from exchange.base_adapter import BaseExchangeAdapter


class MEXCAdapter(BaseExchangeAdapter):
    name = "MEXC"
    supports_real_data = True
    base_urls = ["https://api.mexc.com", "https://www.mexc.com"]

    async def _get_mexc(self, path: str, params: dict[str, Any], label: str) -> Any:
        last_error: Exception | None = None
        for base_url in self.base_urls:
            try:
                return await self._get_json(f"{base_url}{path}", params, f"{label} {base_url}")
            except Exception as error:
                last_error = error
                continue
        raise RuntimeError(str(last_error) if last_error else f"{label} failed")

    async def _spot_ticker_list(self) -> list[dict[str, Any]]:
        cached = self._cache_get("mexc:spot_tickers")
        if cached is not None:
            return cached
        rows = await self._get_mexc("/api/v3/ticker/24hr", {}, "MEXC spot tickers")
        return self._cache_set("mexc:spot_tickers", rows)

    async def fetch_top_symbols(self, limit: int = 20) -> list[str]:
        rows = [
            (item["symbol"], float(item.get("quoteVolume") or 0))
            for item in await self._spot_ticker_list()
            if item.get("symbol", "").endswith("USDT")
        ]
        symbols = [symbol for symbol, _ in sorted(rows, key=lambda item: item[1], reverse=True)[:limit]]
        self.last_top_symbols = symbols
        return symbols

    async def fetch_tickers(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        self.last_error = None
        self.last_source = "spot"
        wanted = set(symbols)
        tickers: dict[str, dict[str, Any]] = {}
        for item in await self._spot_ticker_list():
            symbol = item.get("symbol")
            if symbol not in wanted:
                continue
            tickers[symbol] = {
                "symbol": symbol,
                "lastPrice": float(item.get("lastPrice") or 0),
                "bestBid": float(item.get("bidPrice") or 0),
                "bestAsk": float(item.get("askPrice") or 0),
                "bidQty": float(item.get("bidQty") or 0),
                "askQty": float(item.get("askQty") or 0),
                "volume24h": float(item.get("quoteVolume") or item.get("volume") or 0),
                "change24h": float(item.get("priceChangePercent") or 0),
                "fundingRate": None,
                "openInterest": None,
            }
        self.last_real_ticker_count = len(tickers)
        self.last_ticker_status = "real" if len(tickers) >= len(symbols) else "partial_real" if tickers else "fallback"
        if not tickers:
            raise RuntimeError(self.last_error or "MEXC ticker request returned no requested symbols")
        return tickers

    async def fetch_orderbook(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        data = await self._get_mexc(
            "/api/v3/depth",
            {"symbol": symbol, "limit": min(limit, 100)},
            f"MEXC orderbook {symbol}",
        )
        self.last_orderbook_status = "real"
        return {
            "symbol": symbol,
            "bids": [[float(price), float(qty)] for price, qty in data.get("bids", [])[:limit]],
            "asks": [[float(price), float(qty)] for price, qty in data.get("asks", [])[:limit]],
        }
