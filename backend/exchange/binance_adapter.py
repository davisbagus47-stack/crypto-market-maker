import asyncio
import json
import logging
from typing import Any

import httpx

from exchange.base_adapter import BaseExchangeAdapter

logger = logging.getLogger("crypto_dashboard.binance")


class BinanceAdapter(BaseExchangeAdapter):
    name = "Binance"
    supports_real_data = True
    spot_base_url = "https://api.binance.com"
    spot_base_urls = [
        "https://api.binance.com",
        "https://data-api.binance.vision",
        "https://api1.binance.com",
        "https://api2.binance.com",
        "https://api3.binance.com",
    ]
    futures_base_url = "https://fapi.binance.com"
    excluded_token_fragments = ("UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT")

    def _format_error(self, label: str, error: Exception) -> str:
        if isinstance(error, httpx.HTTPStatusError):
            body = error.response.text[:500] if error.response is not None else ""
            return f"{label}: HTTP {error.response.status_code} {body}"
        return f"{label}: {type(error).__name__}: {error}"

    def _record_error(self, label: str, error: Exception) -> None:
        message = self._format_error(label, error)
        self.last_error = message
        logger.warning("Binance request failed: %s", message)

    def _is_ssl_verify_error(self, error: Exception) -> bool:
        return "CERTIFICATE_VERIFY_FAILED" in str(error) or "Hostname mismatch" in str(error)

    async def _get_json(self, url: str, params: dict[str, Any], label: str) -> Any:
        errors: list[str] = []
        headers = {
            "Accept": "application/json,text/plain,*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
        }
        for verify in (True, False):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, verify=verify, follow_redirects=True, headers=headers) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    try:
                        data = response.json()
                    except ValueError as error:
                        snippet = response.text[:180].replace("\n", " ").replace("\r", " ")
                        raise RuntimeError(f"{label}: non-json response from exchange: {snippet}") from error
                    if verify is False:
                        logger.warning(
                            "Binance public REST succeeded with SSL verification disabled for %s",
                            label,
                        )
                    return data
            except Exception as error:
                message = self._format_error(label, error)
                errors.append(message)
                self._record_error(label, error)
                if verify is True and self._is_ssl_verify_error(error):
                    continue
                if verify is True:
                    break
        raise RuntimeError("; ".join(errors))

    async def fetch_tickers(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        self.last_error = None
        self.last_ticker_status = "fallback"
        self.last_real_ticker_count = 0
        try:
            tickers = await self._fetch_spot_tickers(symbols)
            if tickers:
                self.last_source = "spot"
                self.last_ticker_status = "real" if len(tickers) >= len(symbols) else "partial_real"
                self.last_real_ticker_count = len(tickers)
                derivatives = await self.fetch_derivatives(symbols)
                for symbol, values in derivatives.items():
                    if symbol in tickers:
                        tickers[symbol].update(values)
                return tickers
        except Exception:
            pass

        try:
            tickers = await self._fetch_futures_tickers(symbols)
            if tickers:
                self.last_source = "futures"
                self.last_ticker_status = "real" if len(tickers) >= len(symbols) else "partial_real"
                self.last_real_ticker_count = len(tickers)
                return tickers
        except Exception:
            pass

        self.last_source = "fallback"
        self.last_ticker_status = "fallback"
        raise RuntimeError(self.last_error or "Binance spot and futures ticker requests failed")

    def _is_preferred_symbol(self, symbol: str) -> bool:
        return symbol.endswith("USDT") and not any(fragment in symbol for fragment in self.excluded_token_fragments)

    async def fetch_top_symbols(self, limit: int = 20) -> list[str]:
        cached = self._cache_get("binance:top_symbols")
        if cached:
            self.last_top_symbols = cached[:limit]
            return self.last_top_symbols
        data = None
        last_error: Exception | None = None
        for base_url in self.spot_base_urls:
            try:
                data = await self._get_json(
                    f"{base_url}/api/v3/ticker/24hr",
                    {},
                    f"spot ticker universe {base_url}",
                )
                break
            except Exception as error:
                last_error = error
                continue
        if data is None:
            raise RuntimeError(str(last_error) if last_error else "Binance ticker universe failed")
        rows = [
            (item["symbol"], float(item.get("quoteVolume") or 0))
            for item in data
            if self._is_preferred_symbol(item.get("symbol", ""))
        ]
        symbols = [symbol for symbol, _ in sorted(rows, key=lambda item: item[1], reverse=True)[:limit]]
        self.last_top_symbols = symbols
        return self._cache_set("binance:top_symbols", symbols)

    async def _fetch_spot_tickers(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        params = {"symbols": json.dumps(symbols, separators=(",", ":"))}
        last_error: Exception | None = None
        data = None
        for base_url in self.spot_base_urls:
            try:
                data = await self._get_json(
                    f"{base_url}/api/v3/ticker/24hr",
                    params,
                    f"spot ticker 24hr {base_url}",
                )
                break
            except Exception as error:
                last_error = error
                continue
        if data is None:
            raise RuntimeError(str(last_error) if last_error else "spot ticker 24hr failed")
        return {
            item["symbol"]: {
                "symbol": item["symbol"],
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
            for item in data
            if item.get("symbol") in symbols
        }

    async def _fetch_futures_tickers(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        tickers: dict[str, dict[str, Any]] = {}
        for symbol in symbols:
            data = await self._get_json(
                f"{self.futures_base_url}/fapi/v1/ticker/24hr",
                {"symbol": symbol},
                f"futures ticker 24hr {symbol}",
            )
            tickers[symbol] = {
                "symbol": symbol,
                "lastPrice": float(data.get("lastPrice") or 0),
                "bestBid": float(data.get("bidPrice") or 0),
                "bestAsk": float(data.get("askPrice") or 0),
                "bidQty": float(data.get("bidQty") or 0),
                "askQty": float(data.get("askQty") or 0),
                "volume24h": float(data.get("quoteVolume") or data.get("volume") or 0),
                "change24h": float(data.get("priceChangePercent") or 0),
                "fundingRate": None,
                "openInterest": None,
            }
        derivatives = await self.fetch_derivatives(symbols)
        for symbol, values in derivatives.items():
            if symbol in tickers:
                tickers[symbol].update(values)
        return tickers

    async def fetch_orderbook(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        try:
            book = await self._fetch_spot_orderbook(symbol, limit)
            self.last_source = "spot" if self.last_source != "futures" else self.last_source
            self.last_orderbook_status = "real"
            return book
        except Exception:
            pass

        try:
            book = await self._fetch_futures_orderbook(symbol, limit)
            self.last_source = "futures"
            self.last_orderbook_status = "real"
            return book
        except Exception:
            self.last_source = "fallback"
            self.last_orderbook_status = "fallback"
            raise RuntimeError(self.last_error or f"Binance depth requests failed for {symbol}")

    async def _fetch_spot_orderbook(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        last_error: Exception | None = None
        data = None
        for base_url in self.spot_base_urls:
            try:
                data = await self._get_json(
                    f"{base_url}/api/v3/depth",
                    {"symbol": symbol, "limit": min(limit, 100)},
                    f"spot depth {symbol} {base_url}",
                )
                break
            except Exception as error:
                last_error = error
                continue
        if data is None:
            raise RuntimeError(str(last_error) if last_error else f"spot depth failed for {symbol}")
        return self._parse_depth(symbol, data, limit)

    async def _fetch_futures_orderbook(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        data = await self._get_json(
            f"{self.futures_base_url}/fapi/v1/depth",
            {"symbol": symbol, "limit": min(limit, 100)},
            f"futures depth {symbol}",
        )
        return self._parse_depth(symbol, data, limit)

    def _parse_depth(self, symbol: str, data: dict[str, Any], limit: int) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "bids": [[float(price), float(qty)] for price, qty in data.get("bids", [])[:limit]],
            "asks": [[float(price), float(qty)] for price, qty in data.get("asks", [])[:limit]],
        }

    async def fetch_derivatives(self, symbols: list[str]) -> dict[str, dict[str, float | None]]:
        semaphore = asyncio.Semaphore(8)

        async def fetch_symbol(client: httpx.AsyncClient, symbol: str) -> tuple[str, dict[str, float | None]]:
            values: dict[str, float | None] = {"fundingRate": None, "openInterest": None}
            async with semaphore:
                try:
                    funding = await client.get(
                        f"{self.futures_base_url}/fapi/v1/premiumIndex",
                        params={"symbol": symbol},
                    )
                    if funding.status_code == 200:
                        values["fundingRate"] = float(funding.json().get("lastFundingRate") or 0)
                except Exception as error:
                    logger.debug("Binance funding request failed for %s: %s", symbol, error)
                try:
                    open_interest = await client.get(
                        f"{self.futures_base_url}/fapi/v1/openInterest",
                        params={"symbol": symbol},
                    )
                    if open_interest.status_code == 200:
                        values["openInterest"] = float(open_interest.json().get("openInterest") or 0)
                except Exception as error:
                    logger.debug("Binance open interest request failed for %s: %s", symbol, error)
            return symbol, values

        headers = {
            "Accept": "application/json,text/plain,*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
        }
        async with httpx.AsyncClient(timeout=self.timeout, verify=False, headers=headers, follow_redirects=True) as client:
            rows = await asyncio.gather(*(fetch_symbol(client, symbol) for symbol in symbols))
        return dict(rows)

    async def debug_symbol(self, symbol: str = "BTCUSDT") -> dict[str, Any]:
        result: dict[str, Any] = {
            "symbol": symbol,
            "spot": {"hosts": []},
            "futures": {},
            "selectedSource": "fallback",
            "lastError": None,
        }
        self.last_error = None

        for base_url in self.spot_base_urls:
            host_result: dict[str, Any] = {"baseUrl": base_url}
            for name, path, params in (
                ("ticker", "/api/v3/ticker/24hr", {"symbol": symbol}),
                ("depth", "/api/v3/depth", {"symbol": symbol, "limit": 5}),
            ):
                url = f"{base_url}{path}"
                try:
                    payload = await self._get_json(url, params, f"debug spot {name} {base_url}")
                    host_result[name] = {
                        "ok": True,
                        "statusCode": 200,
                        "url": url,
                        "sample": payload if name == "ticker" else {"bids": payload.get("bids", [])[:1], "asks": payload.get("asks", [])[:1]} if isinstance(payload, dict) else payload,
                    }
                except Exception as error:
                    message = self._format_error(f"debug spot {name} {base_url}", error)
                    host_result[name] = {"ok": False, "url": url, "error": message}
                    result["lastError"] = message
            host_result["ok"] = bool(
                host_result.get("ticker", {}).get("ok") and host_result.get("depth", {}).get("ok")
            )
            result["spot"]["hosts"].append(host_result)
            if host_result["ok"] and result["selectedSource"] == "fallback":
                result["selectedSource"] = "spot"
                result["spot"]["baseUrl"] = base_url
                result["spot"]["ticker"] = host_result["ticker"]
                result["spot"]["depth"] = host_result["depth"]

        for name, url, params in (
            ("ticker", f"{self.futures_base_url}/fapi/v1/ticker/24hr", {"symbol": symbol}),
            ("depth", f"{self.futures_base_url}/fapi/v1/depth", {"symbol": symbol, "limit": 5}),
        ):
            try:
                payload = await self._get_json(url, params, f"debug futures {name}")
                result["futures"][name] = {
                    "ok": True,
                    "statusCode": 200,
                    "url": url,
                    "sample": payload if name == "ticker" else {"bids": payload.get("bids", [])[:1], "asks": payload.get("asks", [])[:1]} if isinstance(payload, dict) else payload,
                }
            except Exception as error:
                message = self._format_error(f"debug futures {name}", error)
                result["futures"][name] = {"ok": False, "url": url, "error": message}
                result["lastError"] = message

        if result["selectedSource"] == "fallback" and result["futures"].get("ticker", {}).get("ok") and result["futures"].get("depth", {}).get("ok"):
            result["selectedSource"] = "futures"
        if result["selectedSource"] == "fallback":
            result["lastError"] = result["lastError"] or self.last_error
        else:
            result["lastError"] = None
        return result
