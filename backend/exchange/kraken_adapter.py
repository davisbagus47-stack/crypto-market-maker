from typing import Any

from exchange.base_adapter import BaseExchangeAdapter


class KrakenAdapter(BaseExchangeAdapter):
    name = "Kraken"
    supports_real_data = True
    base_url = "https://api.kraken.com"

    def __init__(self, timeout: float = 6.0) -> None:
        super().__init__(timeout)
        self.symbol_to_pair: dict[str, str] = {}

    def _normalize_base(self, base: str) -> str:
        return "BTC" if base == "XBT" else base.replace(".", "")

    async def _get_kraken(self, path: str, params: dict[str, Any], label: str) -> Any:
        payload = await self._get_json(f"{self.base_url}{path}", params, label)
        errors = payload.get("error") or []
        if errors:
            raise RuntimeError("; ".join(errors))
        return payload.get("result", {})

    async def _asset_pairs(self) -> dict[str, dict[str, str]]:
        cached = self._cache_get("kraken:asset_pairs", ttl=300)
        if cached is not None:
            return cached
        result = await self._get_kraken("/0/public/AssetPairs", {}, "Kraken asset pairs")
        pairs: dict[str, dict[str, str]] = {}
        for pair_key, item in result.items():
            wsname = item.get("wsname") or ""
            if not wsname.endswith("/USDT") or "/" not in wsname:
                continue
            base = self._normalize_base(wsname.split("/")[0])
            symbol = f"{base}USDT"
            api_pair = item.get("altname") or pair_key
            pairs[symbol] = {"apiPair": api_pair, "responseKey": pair_key, "wsname": wsname}
            self.symbol_to_pair[symbol] = api_pair
        return self._cache_set("kraken:asset_pairs", pairs)

    async def _ticker_map(self) -> dict[str, dict[str, Any]]:
        cached = self._cache_get("kraken:tickers")
        if cached is not None:
            return cached
        pairs = await self._asset_pairs()
        if not pairs:
            raise RuntimeError("Kraken returned no USDT asset pairs")
        result: dict[str, dict[str, Any]] = {}
        symbols = list(pairs.keys())
        for offset in range(0, len(symbols), 40):
            chunk = symbols[offset : offset + 40]
            pair_param = ",".join(pairs[symbol]["apiPair"] for symbol in chunk)
            payload = await self._get_kraken("/0/public/Ticker", {"pair": pair_param}, "Kraken tickers")
            by_api_pair = {pairs[symbol]["apiPair"]: symbol for symbol in chunk}
            by_response_key = {pairs[symbol]["responseKey"]: symbol for symbol in chunk}
            for response_key, item in payload.items():
                symbol = by_api_pair.get(response_key) or by_response_key.get(response_key)
                if not symbol:
                    normalized = response_key.replace("XBT", "BTC").replace("/", "").replace(".", "")
                    symbol = normalized if normalized.endswith("USDT") else ""
                if symbol:
                    result[symbol] = item
        return self._cache_set("kraken:tickers", result)

    async def fetch_top_symbols(self, limit: int = 20) -> list[str]:
        rows = []
        for symbol, item in (await self._ticker_map()).items():
            last_price = float((item.get("c") or [0])[0] or 0)
            base_volume = float((item.get("v") or [0, 0])[1] or 0)
            rows.append((symbol, last_price * base_volume))
        symbols = [symbol for symbol, _ in sorted(rows, key=lambda item: item[1], reverse=True)[:limit]]
        self.last_top_symbols = symbols
        return symbols

    async def fetch_tickers(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        self.last_error = None
        self.last_source = "spot"
        tickers: dict[str, dict[str, Any]] = {}
        ticker_map = await self._ticker_map()
        for symbol in symbols:
            item = ticker_map.get(symbol)
            if not item:
                continue
            last_price = float((item.get("c") or [0])[0] or 0)
            open_price = float(item.get("o") or 0)
            tickers[symbol] = {
                "symbol": symbol,
                "lastPrice": last_price,
                "bestBid": float((item.get("b") or [0])[0] or 0),
                "bestAsk": float((item.get("a") or [0])[0] or 0),
                "bidQty": float((item.get("b") or [0, 0])[1] or 0),
                "askQty": float((item.get("a") or [0, 0])[1] or 0),
                "volume24h": last_price * float((item.get("v") or [0, 0])[1] or 0),
                "change24h": ((last_price - open_price) / open_price * 100) if open_price else 0,
                "fundingRate": None,
                "openInterest": None,
            }
        self.last_real_ticker_count = len(tickers)
        self.last_ticker_status = "real" if len(tickers) >= len(symbols) else "partial_real" if tickers else "fallback"
        if not tickers:
            raise RuntimeError(self.last_error or "Kraken ticker request returned no requested symbols")
        return tickers

    async def fetch_orderbook(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        pairs = await self._asset_pairs()
        api_pair = pairs.get(symbol, {}).get("apiPair") or self.symbol_to_pair.get(symbol)
        if not api_pair:
            raise RuntimeError(f"Kraken has no USDT pair mapping for {symbol}")
        result = await self._get_kraken(
            "/0/public/Depth",
            {"pair": api_pair, "count": min(limit, 100)},
            f"Kraken orderbook {symbol}",
        )
        if not result:
            raise RuntimeError(f"Kraken orderbook returned no data for {symbol}")
        book = next(iter(result.values()))
        self.last_orderbook_status = "real"
        return {
            "symbol": symbol,
            "bids": [[float(level[0]), float(level[1])] for level in book.get("bids", [])[:limit]],
            "asks": [[float(level[0]), float(level[1])] for level in book.get("asks", [])[:limit]],
        }
