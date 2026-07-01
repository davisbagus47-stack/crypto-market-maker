from typing import Any

from exchange.base_adapter import BaseExchangeAdapter


class OKXAdapter(BaseExchangeAdapter):
    name = "OKX"
    supports_real_data = True
    base_urls = ["https://www.okx.com", "https://aws.okx.com"]

    def _to_inst_id(self, symbol: str) -> str:
        if "-" in symbol:
            return symbol
        return symbol.replace("USDT", "-USDT")

    def _to_symbol(self, inst_id: str) -> str:
        return inst_id.replace("-", "")

    async def _get_okx(self, path: str, params: dict[str, Any], label: str) -> Any:
        last_error: Exception | None = None
        for base_url in self.base_urls:
            try:
                payload = await self._get_json(f"{base_url}{path}", params, f"{label} {base_url}")
                if payload.get("code") not in ("0", 0, None):
                    raise RuntimeError(payload.get("msg") or "OKX returned non-zero code")
                return payload.get("data", [])
            except Exception as error:
                last_error = error
                continue
        raise RuntimeError(str(last_error) if last_error else f"{label} failed")

    async def _spot_ticker_list(self) -> list[dict[str, Any]]:
        cached = self._cache_get("okx:spot_tickers")
        if cached is not None:
            return cached
        rows = await self._get_okx("/api/v5/market/tickers", {"instType": "SPOT"}, "OKX spot tickers")
        return self._cache_set("okx:spot_tickers", rows)

    async def fetch_top_symbols(self, limit: int = 20) -> list[str]:
        rows = [
            (self._to_symbol(item["instId"]), float(item.get("volCcy24h") or item.get("vol24h") or 0))
            for item in await self._spot_ticker_list()
            if item.get("instId", "").endswith("-USDT")
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
            symbol = self._to_symbol(item.get("instId", ""))
            if symbol not in wanted:
                continue
            last_price = float(item.get("last") or 0)
            open_price = float(item.get("open24h") or 0)
            change = ((last_price - open_price) / open_price * 100) if open_price else 0
            tickers[symbol] = {
                "symbol": symbol,
                "lastPrice": last_price,
                "bestBid": float(item.get("bidPx") or 0),
                "bestAsk": float(item.get("askPx") or 0),
                "bidQty": float(item.get("bidSz") or 0),
                "askQty": float(item.get("askSz") or 0),
                "volume24h": float(item.get("volCcy24h") or 0),
                "change24h": change,
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
            raise RuntimeError(self.last_error or "OKX ticker request returned no requested symbols")
        return tickers

    async def fetch_orderbook(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        rows = await self._get_okx(
            "/api/v5/market/books",
            {"instId": self._to_inst_id(symbol), "sz": min(limit, 50)},
            f"OKX orderbook {symbol}",
        )
        if not rows:
            raise RuntimeError(f"OKX orderbook returned no data for {symbol}")
        book = rows[0]
        self.last_orderbook_status = "real"
        return {
            "symbol": symbol,
            "bids": [[float(level[0]), float(level[1])] for level in book.get("bids", [])[:limit]],
            "asks": [[float(level[0]), float(level[1])] for level in book.get("asks", [])[:limit]],
        }

    async def fetch_derivatives(self, symbols: list[str]) -> dict[str, dict[str, float | None]]:
        values = {symbol: {"fundingRate": None, "openInterest": None} for symbol in symbols}
        for symbol in symbols:
            swap_id = self._to_inst_id(symbol).replace("-USDT", "-USDT-SWAP")
            try:
                rows = await self._get_okx(
                    "/api/v5/public/funding-rate",
                    {"instId": swap_id},
                    f"OKX funding {symbol}",
                )
                if rows:
                    values[symbol]["fundingRate"] = float(rows[0].get("fundingRate") or 0)
            except Exception:
                continue
        return values
