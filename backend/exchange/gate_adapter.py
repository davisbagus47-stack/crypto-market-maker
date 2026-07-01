from typing import Any

from exchange.base_adapter import BaseExchangeAdapter


class GateAdapter(BaseExchangeAdapter):
    name = "Gate.io"
    supports_real_data = True
    base_url = "https://api.gateio.ws"

    def _to_pair(self, symbol: str) -> str:
        return symbol.replace("USDT", "_USDT")

    def _to_symbol(self, pair: str) -> str:
        return pair.replace("_", "")

    async def _spot_ticker_list(self) -> list[dict[str, Any]]:
        cached = self._cache_get("gate:spot_tickers")
        if cached is not None:
            return cached
        rows = await self._get_json(
            f"{self.base_url}/api/v4/spot/tickers",
            {},
            "Gate.io spot tickers",
            headers={"Accept": "application/json"},
        )
        return self._cache_set("gate:spot_tickers", rows)

    async def fetch_top_symbols(self, limit: int = 20) -> list[str]:
        rows = [
            (self._to_symbol(item["currency_pair"]), float(item.get("quote_volume") or 0))
            for item in await self._spot_ticker_list()
            if item.get("currency_pair", "").endswith("_USDT")
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
            symbol = self._to_symbol(item.get("currency_pair", ""))
            if symbol not in wanted:
                continue
            last_price = float(item.get("last") or 0)
            tickers[symbol] = {
                "symbol": symbol,
                "lastPrice": last_price,
                "bestBid": float(item.get("highest_bid") or 0),
                "bestAsk": float(item.get("lowest_ask") or 0),
                "bidQty": 0,
                "askQty": 0,
                "volume24h": float(item.get("quote_volume") or 0),
                "change24h": float(item.get("change_percentage") or 0),
                "fundingRate": None,
                "openInterest": None,
            }
        self.last_real_ticker_count = len(tickers)
        self.last_ticker_status = "real" if len(tickers) >= len(symbols) else "partial_real" if tickers else "fallback"
        if not tickers:
            raise RuntimeError(self.last_error or "Gate.io ticker request returned no requested symbols")
        return tickers

    async def fetch_orderbook(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        data = await self._get_json(
            f"{self.base_url}/api/v4/spot/order_book",
            {"currency_pair": self._to_pair(symbol), "limit": min(limit, 100)},
            f"Gate.io orderbook {symbol}",
            headers={"Accept": "application/json"},
        )
        self.last_orderbook_status = "real"
        return {
            "symbol": symbol,
            "bids": [[float(price), float(qty)] for price, qty in data.get("bids", [])[:limit]],
            "asks": [[float(price), float(qty)] for price, qty in data.get("asks", [])[:limit]],
        }
