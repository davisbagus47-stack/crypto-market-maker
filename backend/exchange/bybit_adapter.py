import asyncio
from typing import Any

from exchange.base_adapter import BaseExchangeAdapter


class BybitAdapter(BaseExchangeAdapter):
    name = "Bybit"
    supports_real_data = True
    base_urls = ["https://api.bybit.com", "https://api.bytick.com"]

    async def _get_bybit(self, path: str, params: dict[str, Any], label: str) -> Any:
        last_error: Exception | None = None
        for base_url in self.base_urls:
            try:
                payload = await self._get_json(f"{base_url}{path}", params, f"{label} {base_url}")
                if payload.get("retCode") not in (0, "0", None):
                    raise RuntimeError(payload.get("retMsg") or "Bybit returned non-zero retCode")
                return payload.get("result", {})
            except Exception as error:
                last_error = error
                continue
        raise RuntimeError(str(last_error) if last_error else f"{label} failed")

    async def _spot_ticker_list(self) -> list[dict[str, Any]]:
        cached = self._cache_get("bybit:spot_tickers")
        if cached is not None:
            return cached
        result = await self._get_bybit("/v5/market/tickers", {"category": "spot"}, "Bybit spot tickers")
        return self._cache_set("bybit:spot_tickers", result.get("list", []))

    async def fetch_top_symbols(self, limit: int = 20) -> list[str]:
        rows = [
            (item["symbol"], float(item.get("turnover24h") or 0))
            for item in await self._spot_ticker_list()
            if item.get("symbol", "").endswith("USDT")
        ]
        symbols = [symbol for symbol, _ in sorted(rows, key=lambda item: item[1], reverse=True)[:limit]]
        self.last_top_symbols = symbols
        return symbols

    async def fetch_tickers(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        self.last_error = None
        self.last_source = "spot"
        rows = await self._spot_ticker_list()
        wanted = set(symbols)
        tickers: dict[str, dict[str, Any]] = {}
        for item in rows:
            symbol = item.get("symbol")
            if symbol not in wanted:
                continue
            last_price = float(item.get("lastPrice") or 0)
            change_raw = float(item.get("price24hPcnt") or 0)
            tickers[symbol] = {
                "symbol": symbol,
                "lastPrice": last_price,
                "bestBid": float(item.get("bid1Price") or 0),
                "bestAsk": float(item.get("ask1Price") or 0),
                "bidQty": float(item.get("bid1Size") or 0),
                "askQty": float(item.get("ask1Size") or 0),
                "volume24h": float(item.get("turnover24h") or 0),
                "change24h": change_raw * 100,
                "fundingRate": None,
                "openInterest": None,
            }
        derivatives = await self.fetch_derivatives(symbols)
        for symbol, values in derivatives.items():
            if symbol in tickers:
                tickers[symbol].update(values)
        self.last_real_ticker_count = len(tickers)
        self.last_ticker_status = "real" if len(tickers) >= len(symbols) else "partial_real" if tickers else "fallback"
        if not tickers:
            raise RuntimeError(self.last_error or "Bybit spot ticker request returned no requested symbols")
        return tickers

    async def fetch_orderbook(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        result = await self._get_bybit(
            "/v5/market/orderbook",
            {"category": "spot", "symbol": symbol, "limit": min(limit, 50)},
            f"Bybit spot orderbook {symbol}",
        )
        self.last_orderbook_status = "real"
        return {
            "symbol": symbol,
            "bids": [[float(price), float(qty)] for price, qty in result.get("b", [])[:limit]],
            "asks": [[float(price), float(qty)] for price, qty in result.get("a", [])[:limit]],
        }

    async def fetch_derivatives(self, symbols: list[str]) -> dict[str, dict[str, float | None]]:
        semaphore = asyncio.Semaphore(8)

        async def fetch_symbol(symbol: str) -> tuple[str, dict[str, float | None]]:
            values: dict[str, float | None] = {"fundingRate": None, "openInterest": None}
            try:
                async with semaphore:
                    result = await self._get_bybit(
                        "/v5/market/tickers",
                        {"category": "linear", "symbol": symbol},
                        f"Bybit linear ticker {symbol}",
                    )
                    rows = result.get("list", [])
                    if rows:
                        row = rows[0]
                        values = {
                            "fundingRate": float(row.get("fundingRate") or 0),
                            "openInterest": float(row.get("openInterest") or 0),
                        }
            except Exception:
                pass
            return symbol, values

        return dict(await asyncio.gather(*(fetch_symbol(symbol) for symbol in symbols)))
