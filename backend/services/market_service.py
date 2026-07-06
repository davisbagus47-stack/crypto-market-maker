import asyncio
import json
import math
import time
from typing import Any

from config import BASE_PRICES, FALLBACK_TOP_SYMBOLS, SYMBOL_DISPLAY, normalize_exchange
from database import compute_window_cutoff, execute_many, fetch_all, interval_to_seconds, now_iso
from exchange.base_adapter import BaseExchangeAdapter
from exchange.binance_adapter import BinanceAdapter
from exchange.bybit_adapter import BybitAdapter
from exchange.gate_adapter import GateAdapter
from exchange.kraken_adapter import KrakenAdapter
from exchange.mexc_adapter import MEXCAdapter
from exchange.okx_adapter import OKXAdapter


ADAPTERS: dict[str, BaseExchangeAdapter] = {
    "Binance": BinanceAdapter(),
    "Bybit": BybitAdapter(),
    "OKX": OKXAdapter(),
    "Gate.io": GateAdapter(),
    "Kraken": KrakenAdapter(),
    "MEXC": MEXCAdapter(),
}
TOP_PAIR_LIMIT = 20


def get_adapter(exchange: str | None) -> BaseExchangeAdapter:
    return ADAPTERS.get(normalize_exchange(exchange), ADAPTERS["Binance"])


def display_symbol(symbol: str) -> str:
    return SYMBOL_DISPLAY.get(symbol, symbol.replace("USDT", "/USDT"))


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def sum_depth(levels: list[list[float]], top: int = 10) -> float:
    return sum(float(price) * float(qty) for price, qty in levels[:top])


def estimate_slippage(asks: list[list[float]], order_size_usdt: float = 100000) -> float:
    if not asks:
        return 0.0
    best_ask = asks[0][0]
    remaining = order_size_usdt
    total_qty = 0.0
    total_cost = 0.0
    for price, qty in asks:
        available = price * qty
        take_usdt = min(remaining, available)
        take_qty = take_usdt / price
        total_qty += take_qty
        total_cost += take_usdt
        remaining -= take_usdt
        if remaining <= 0:
            break
    if total_qty <= 0:
        return 0.0
    avg_price = total_cost / total_qty
    return max(0.0, ((avg_price - best_ask) / best_ask) * 100)


def liquidity_score(spread_pct: float, bid_depth: float, ask_depth: float, imbalance: float, slippage: float) -> float:
    total_depth = bid_depth + ask_depth
    depth_score = clamp(math.log10(max(total_depth, 1)) * 12)
    spread_penalty = min(45, spread_pct * 950)
    imbalance_penalty = min(22, abs(imbalance) * 38)
    slippage_penalty = min(22, slippage * 360)
    return round(clamp(72 + depth_score / 2 - spread_penalty - imbalance_penalty - slippage_penalty), 2)


def market_cap_estimate(symbol: str, last_price: float) -> float:
    supply = {
        "BTCUSDT": 19_700_000,
        "ETHUSDT": 120_000_000,
        "SOLUSDT": 470_000_000,
        "XRPUSDT": 56_000_000_000,
        "BNBUSDT": 147_000_000,
        "ADAUSDT": 35_000_000_000,
        "DOGEUSDT": 144_000_000_000,
        "AVAXUSDT": 407_000_000,
    }.get(symbol, 100_000_000)
    return last_price * supply


def compute_pair_metrics(
    exchange: str,
    symbol: str,
    ticker: dict[str, Any],
    orderbook: dict[str, Any],
) -> dict[str, Any]:
    bids = orderbook.get("bids") or []
    asks = orderbook.get("asks") or []
    best_bid = float(ticker.get("bestBid") or (bids[0][0] if bids else 0))
    best_ask = float(ticker.get("bestAsk") or (asks[0][0] if asks else 0))
    last_price = float(ticker.get("lastPrice") or BASE_PRICES.get(symbol, 100))
    bid_qty = float(ticker.get("bidQty") or (bids[0][1] if bids else 0))
    ask_qty = float(ticker.get("askQty") or (asks[0][1] if asks else 0))
    if best_bid <= 0 and bids:
        best_bid = bids[0][0]
    if best_ask <= 0 and asks:
        best_ask = asks[0][0]
    spread = max(0.0, best_ask - best_bid)
    spread_pct = ((spread / best_ask) * 100) if best_ask else 0.0
    bid_depth = sum_depth(bids, 10)
    ask_depth = sum_depth(asks, 10)
    imbalance = ((bid_depth - ask_depth) / (bid_depth + ask_depth)) if (bid_depth + ask_depth) else 0.0
    slippage = estimate_slippage(asks, 100000)
    score = liquidity_score(spread_pct, bid_depth, ask_depth, imbalance, slippage)
    change_24h = float(ticker.get("change24h") or 0)
    volume_24h = float(ticker.get("volume24h") or 0)
    funding = ticker.get("fundingRate")
    open_interest = ticker.get("openInterest")
    spread_volatility = abs(math.sin(time.time() / 45 + len(symbol))) * spread_pct * 2.4
    order_flow_imbalance = imbalance + math.sin(time.time() / 60 + len(symbol)) * 0.035
    market_impact = slippage * 0.72 + spread_pct * 0.2

    return {
        "exchange": exchange,
        "symbol": display_symbol(symbol),
        "displaySymbol": display_symbol(symbol),
        "key": symbol,
        "price": round(last_price, 8),
        "lastPrice": round(last_price, 8),
        "bestBid": round(best_bid, 8),
        "bestAsk": round(best_ask, 8),
        "bidQty": round(bid_qty, 8),
        "askQty": round(ask_qty, 8),
        "spread": round(spread_pct, 6),
        "spreadAbs": round(spread, 8),
        "spreadPct": round(spread_pct, 6),
        "maxSpread": round(spread_pct * 3.5, 6),
        "change": round(change_24h, 4),
        "change24h": round(change_24h, 4),
        "volume": round(volume_24h / 1_000_000_000, 4),
        "volume24h": round(volume_24h, 2),
        "marketCap": round(market_cap_estimate(symbol, last_price) / 1_000_000_000, 4),
        "futuresVol": round((volume_24h * 1.75) / 1_000_000_000, 4),
        "oi": round((float(open_interest or 0) * last_price) / 1_000_000_000, 4) if open_interest else round(volume_24h * 0.31 / 1_000_000_000, 4),
        "funding": round(float(funding or 0) * 100, 5),
        "basis": round(spread_pct / 3, 4),
        "bidDepth": round(bid_depth, 2),
        "askDepth": round(ask_depth, 2),
        "imbalance": round(imbalance, 6),
        "slippage": round(slippage, 6),
        "liquidity": score,
        "resilience": round(clamp(score / 100 - abs(imbalance) * 0.15, 0, 1), 4),
        "regime": "High" if score >= 75 else "Medium" if score >= 55 else "Low",
        "ofi": round(order_flow_imbalance, 6),
        "volatility": round(spread_volatility, 6),
        "impact": round(market_impact, 6),
        "bids": bids,
        "asks": asks,
        "timestamp": now_iso(),
    }


async def get_market_data(
    exchange: str | None,
    symbols: list[str] | None = None,
    interval: str = "5m",
    persist: bool = True,
    limit: int = TOP_PAIR_LIMIT,
) -> dict[str, Any]:
    selected_exchange = normalize_exchange(exchange)
    adapter = get_adapter(selected_exchange)
    selected_symbols = symbols[:] if symbols else []
    requested_symbols = bool(selected_symbols)
    source_status = "fallback"
    exchange_errors: list[str] = []
    top_symbols_failed = False

    if not selected_symbols:
        try:
            selected_symbols = await adapter.fetch_top_symbols(limit)
        except Exception as error:
            top_symbols_failed = True
            exchange_errors.append(f"top symbols: {error}")
            selected_symbols = FALLBACK_TOP_SYMBOLS[:limit]
            adapter.last_top_symbols = selected_symbols[:]
    selected_symbols = selected_symbols[:limit] or FALLBACK_TOP_SYMBOLS[:limit]
    adapter.last_top_symbols = selected_symbols[:]

    ticker_real_count = 0
    try:
        real_tickers = await adapter.fetch_tickers(selected_symbols)
        ticker_real_count = len(real_tickers)
        mock_tickers = adapter.mock_tickers(selected_symbols)
        tickers = {
            symbol: real_tickers.get(symbol) or mock_tickers[symbol]
            for symbol in selected_symbols
        }
    except Exception as error:
        exchange_errors.append(f"tickers: {error}")
        tickers = adapter.mock_tickers(selected_symbols)
        ticker_real_count = 0

    orderbook_errors: list[str] = []

    async def fetch_book(symbol: str) -> tuple[str, dict[str, Any], bool, str | None]:
        if top_symbols_failed and not requested_symbols and ticker_real_count == 0:
            fallback_price = float(tickers.get(symbol, {}).get("lastPrice") or BASE_PRICES.get(symbol, 100))
            return symbol, adapter.mock_orderbook(symbol, fallback_price, limit=20), False, None
        try:
            book = await adapter.fetch_orderbook(symbol, limit=20)
            return symbol, book, bool(book.get("bids") and book.get("asks")), None
        except Exception as error:
            fallback_price = float(tickers.get(symbol, {}).get("lastPrice") or BASE_PRICES.get(symbol, 100))
            return symbol, adapter.mock_orderbook(symbol, fallback_price, limit=20), False, f"{symbol}: {error}"

    semaphore = asyncio.Semaphore(8)

    async def guarded_fetch_book(symbol: str) -> tuple[str, dict[str, Any], bool, str | None]:
        async with semaphore:
            return await fetch_book(symbol)

    book_results = await asyncio.gather(*(guarded_fetch_book(symbol) for symbol in selected_symbols))
    orderbooks = {symbol: book for symbol, book, _, _ in book_results}
    orderbook_real_count = sum(1 for _, _, is_real, _ in book_results if is_real)
    orderbook_errors = [error for _, _, _, error in book_results if error]
    if orderbook_errors:
        exchange_errors.append("orderbooks: " + "; ".join(orderbook_errors[:5]))

    total_symbols = len(selected_symbols)
    ticker_status = "real" if ticker_real_count >= total_symbols else "partial_real" if ticker_real_count else "fallback"
    orderbook_status = (
        "real"
        if orderbook_real_count >= total_symbols
        else "partial_real"
        if orderbook_real_count
        else "fallback"
    )
    adapter.last_real_ticker_count = ticker_real_count
    adapter.last_real_orderbook_count = orderbook_real_count
    adapter.last_ticker_status = ticker_status
    adapter.last_orderbook_status = orderbook_status

    if ticker_status == "real" and orderbook_status == "real":
        source_status = "real"
    elif ticker_real_count or orderbook_real_count:
        source_status = "partial_real"
    exchange_error = "; ".join(exchange_errors) if exchange_errors else None
    if adapter.last_error and (source_status == "fallback" or exchange_error):
        exchange_error = exchange_error or adapter.last_error

    pairs = [
        compute_pair_metrics(selected_exchange, symbol, tickers.get(symbol, {}), orderbooks.get(symbol, {}))
        for symbol in selected_symbols
    ]
    if persist:
        await persist_market_data(pairs)
    return {
        "exchange": selected_exchange,
        "interval": interval,
        "sourceStatus": source_status,
        "tickerStatus": ticker_status,
        "orderbookStatus": orderbook_status,
        "symbolCount": len(selected_symbols),
        "topSymbols": selected_symbols,
        "realTickerCount": ticker_real_count,
        "realOrderbookCount": orderbook_real_count,
        "exchangeError": exchange_error,
        "exchangeSource": adapter.last_source,
        "lastUpdate": now_iso(),
        "pairs": pairs,
    }


async def debug_exchange(exchange: str, limit: int = TOP_PAIR_LIMIT) -> dict[str, Any]:
    market = await get_market_data(exchange, None, "5m", persist=False, limit=limit)
    return {
        "exchange": market["exchange"],
        "sourceStatus": market["sourceStatus"],
        "tickerStatus": market["tickerStatus"],
        "orderbookStatus": market["orderbookStatus"],
        "symbolCount": market["symbolCount"],
        "realTickerCount": market["realTickerCount"],
        "realOrderbookCount": market["realOrderbookCount"],
        "topSymbols": market["topSymbols"],
        "lastError": market.get("exchangeError"),
    }


async def debug_all_exchanges(limit: int = TOP_PAIR_LIMIT) -> list[dict[str, Any]]:
    results = []
    for exchange_name in ADAPTERS:
        results.append(await debug_exchange(exchange_name, limit=limit))
    return results


async def persist_market_data(pairs: list[dict[str, Any]]) -> None:
    market_rows = []
    orderbook_rows = []
    timestamp = now_iso()
    for pair in pairs:
        market_rows.append(
            (
                timestamp,
                pair["exchange"],
                pair["key"],
                pair["lastPrice"],
                pair["bestBid"],
                pair["bestAsk"],
                pair["bidQty"],
                pair["askQty"],
                pair["spreadAbs"],
                pair["spreadPct"],
                pair["volume24h"],
                pair["change24h"],
                pair["funding"],
                pair["oi"],
                timestamp,
            )
        )
        orderbook_rows.append(
            (
                timestamp,
                pair["exchange"],
                pair["key"],
                json.dumps(pair["bids"]),
                json.dumps(pair["asks"]),
                pair["bidDepth"],
                pair["askDepth"],
                pair["imbalance"],
                pair["slippage"],
                pair["liquidity"],
                timestamp,
            )
        )
    await execute_many(
        """
        INSERT INTO market_snapshots (
            timestamp, exchange, symbol, last_price, best_bid, best_ask, bid_qty, ask_qty,
            spread, spread_pct, volume_24h, change_24h, funding_rate, open_interest, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        market_rows,
    )
    await execute_many(
        """
        INSERT INTO orderbook_snapshots (
            timestamp, exchange, symbol, bids_json, asks_json, bid_depth_top10, ask_depth_top10,
            imbalance, slippage_100k, liquidity_score, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        orderbook_rows,
    )


# ---------------------------------------------------------------------------
# Moving-window aggregation: query historical snapshots from SQLite
# ---------------------------------------------------------------------------

# Thresholds for choosing aggregation strategy
_SHORT_INTERVAL_SECONDS = 30  # <=30s uses real-time snapshot
_LONG_INTERVAL_SECONDS = 86400  # >=1D uses downsampling


def _downsample_group_seconds(interval: str) -> int:
    """Return the bucket size (seconds) for downsampling long timeframes."""
    total = interval_to_seconds(interval)
    if total >= 86400 * 25:  # ~1M or more → daily buckets
        return 86400
    if total >= 86400 * 3:  # >=3D → 4-hour buckets
        return 14400
    if total >= 86400:  # >=1D → hourly buckets
        return 3600
    return 300  # fallback: 5-min buckets


async def get_aggregated_market_data(
    exchange: str | None,
    symbols: list[str] | None = None,
    interval: str = "5m",
) -> dict[str, Any]:
    """
    Return market metrics aggregated over a moving time window.

    For intervals <= 30s this falls back to the real-time snapshot path
    (there is not enough historical data to aggregate meaningfully).

    For longer intervals it queries the ``market_snapshots`` table, sums
    bid_qty / ask_qty over the window, and recomputes imbalance with the
    correct sign convention (positive → Buyer Dominant).

    For very long intervals (>= 1 day) the raw per-second rows are
    downsampled into time buckets to keep the query fast.
    """
    selected_exchange = normalize_exchange(exchange)
    total_seconds = interval_to_seconds(interval)

    # Short intervals → use live snapshot (no historical aggregation)
    if total_seconds <= _SHORT_INTERVAL_SECONDS:
        return await get_market_data(selected_exchange, symbols, interval, persist=False)

    selected_symbols = symbols[:] if symbols else FALLBACK_TOP_SYMBOLS[:TOP_PAIR_LIMIT]

    cutoff = compute_window_cutoff(interval)
    symbol_list = ",".join(f"'{s}'" for s in selected_symbols)

    # ---- Build the aggregation query ----
    # For long timeframes we downsample into time buckets to avoid scanning
    # millions of rows.  Each bucket becomes one "virtual snapshot" whose
    # bid_qty / ask_qty are the SUM within that bucket.
    if total_seconds >= _LONG_INTERVAL_SECONDS:
        bucket_sec = _downsample_group_seconds(interval)
        # SQLite: group by strftime('%Y-%m-%d %H:', timestamp) for hourly, etc.
        # We use a simpler approach: assign each row to a bucket number
        # based on (julianday(timestamp) * 86400 / bucket_sec)
        query = f"""
            SELECT
                symbol,
                SUM(bid_qty)   AS total_bid_qty,
                SUM(ask_qty)   AS total_ask_qty,
                AVG(last_price) AS avg_last_price,
                AVG(best_bid)  AS avg_best_bid,
                AVG(best_ask)  AS avg_best_ask,
                AVG(spread_pct) AS avg_spread_pct,
                AVG(volume_24h) AS avg_volume_24h,
                AVG(change_24h) AS avg_change_24h,
                COUNT(*)       AS snapshot_count
            FROM market_snapshots
            WHERE exchange = ?
              AND symbol IN ({symbol_list})
              AND timestamp >= ?
            GROUP BY symbol,
                     CAST((julianday(timestamp) * 86400.0 / {bucket_sec}) AS INTEGER)
        """
    else:
        # Medium intervals (1m – 12h): aggregate all snapshots in the window
        query = f"""
            SELECT
                symbol,
                SUM(bid_qty)    AS total_bid_qty,
                SUM(ask_qty)    AS total_ask_qty,
                AVG(last_price)  AS avg_last_price,
                AVG(best_bid)    AS avg_best_bid,
                AVG(best_ask)    AS avg_best_ask,
                AVG(spread_pct)  AS avg_spread_pct,
                AVG(volume_24h)  AS avg_volume_24h,
                AVG(change_24h)  AS avg_change_24h,
                COUNT(*)         AS snapshot_count
            FROM market_snapshots
            WHERE exchange = ?
              AND symbol IN ({symbol_list})
              AND timestamp >= ?
            GROUP BY symbol
        """

    rows = await fetch_all(query, (selected_exchange, cutoff))

    # Build a lookup: symbol → aggregated values
    agg_map: dict[str, dict] = {}
    for row in rows:
        sym = row["symbol"]
        if sym not in agg_map:
            agg_map[sym] = {
                "total_bid_qty": 0.0,
                "total_ask_qty": 0.0,
                "avg_last_price": 0.0,
                "avg_best_bid": 0.0,
                "avg_best_ask": 0.0,
                "avg_spread_pct": 0.0,
                "avg_volume_24h": 0.0,
                "avg_change_24h": 0.0,
                "snapshot_count": 0,
                "bucket_count": 0,
            }
        agg_map[sym]["total_bid_qty"] += float(row["total_bid_qty"] or 0)
        agg_map[sym]["total_ask_qty"] += float(row["total_ask_qty"] or 0)
        # For averages we take a weighted average across buckets
        agg_map[sym]["avg_last_price"] += float(row["avg_last_price"] or 0)
        agg_map[sym]["avg_best_bid"] += float(row["avg_best_bid"] or 0)
        agg_map[sym]["avg_best_ask"] += float(row["avg_best_ask"] or 0)
        agg_map[sym]["avg_spread_pct"] += float(row["avg_spread_pct"] or 0)
        agg_map[sym]["avg_volume_24h"] += float(row["avg_volume_24h"] or 0)
        agg_map[sym]["avg_change_24h"] += float(row["avg_change_24h"] or 0)
        agg_map[sym]["snapshot_count"] += int(row["snapshot_count"] or 0)
        agg_map[sym]["bucket_count"] += 1

    # Finalize averages (divide by number of buckets)
    for sym, data in agg_map.items():
        bc = max(data["bucket_count"], 1)
        data["avg_last_price"] /= bc
        data["avg_best_bid"] /= bc
        data["avg_best_ask"] /= bc
        data["avg_spread_pct"] /= bc
        data["avg_volume_24h"] /= bc
        data["avg_change_24h"] /= bc

    # Build pair metrics from aggregated data
    pairs = []
    for symbol in selected_symbols:
        agg = agg_map.get(symbol)
        if not agg or agg["snapshot_count"] == 0:
            # No historical data for this symbol in the window — skip
            continue

        total_bid = agg["total_bid_qty"]
        total_ask = agg["total_ask_qty"]
        last_price = agg["avg_last_price"]
        best_bid = agg["avg_best_bid"]
        best_ask = agg["avg_best_ask"]
        spread_pct = agg["avg_spread_pct"]

        # Correct imbalance formula: (bid - ask) / (bid + ask)
        # Positive → Buyer Dominant, Negative → Seller Dominant
        total_depth = total_bid + total_ask
        imbalance = ((total_bid - total_ask) / total_depth) if total_depth > 0 else 0.0

        # For aggregated data, bidDepth/askDepth represent the summed top-of-book
        # quantity over the window — a measure of cumulative liquidity
        bid_depth = total_bid * (best_bid if best_bid > 0 else 1)
        ask_depth = total_ask * (best_ask if best_ask > 0 else 1)

        score = liquidity_score(spread_pct, bid_depth, ask_depth, imbalance, 0.0)

        pairs.append({
            "exchange": selected_exchange,
            "symbol": display_symbol(symbol),
            "displaySymbol": display_symbol(symbol),
            "key": symbol,
            "price": round(last_price, 8),
            "lastPrice": round(last_price, 8),
            "bestBid": round(best_bid, 8),
            "bestAsk": round(best_ask, 8),
            "bidQty": round(total_bid, 8),
            "askQty": round(total_ask, 8),
            "spread": round(spread_pct, 6),
            "spreadAbs": round((best_ask - best_bid) if best_ask and best_bid else 0, 8),
            "spreadPct": round(spread_pct, 6),
            "maxSpread": round(spread_pct * 3.5, 6),
            "change": round(agg["avg_change_24h"], 4),
            "change24h": round(agg["avg_change_24h"], 4),
            "volume": round(agg["avg_volume_24h"] / 1_000_000_000, 4),
            "volume24h": round(agg["avg_volume_24h"], 2),
            "marketCap": round(market_cap_estimate(symbol, last_price) / 1_000_000_000, 4),
            "futuresVol": round((agg["avg_volume_24h"] * 1.75) / 1_000_000_000, 4),
            "oi": round(agg["avg_volume_24h"] * 0.31 / 1_000_000_000, 4),
            "funding": 0.0,
            "basis": round(spread_pct / 3, 4),
            "bidDepth": round(bid_depth, 2),
            "askDepth": round(ask_depth, 2),
            "imbalance": round(imbalance, 6),
            "slippage": 0.0,
            "liquidity": score,
            "resilience": round(clamp(score / 100 - abs(imbalance) * 0.15, 0, 1), 4),
            "regime": "High" if score >= 75 else "Medium" if score >= 55 else "Low",
            "ofi": round(imbalance, 6),
            "volatility": round(abs(imbalance) * 2.4, 6),
            "impact": round(spread_pct * 0.2, 6),
            "bids": [],
            "asks": [],
            "timestamp": now_iso(),
            "aggregated": True,
            "snapshotCount": agg["snapshot_count"],
            "interval": interval,
        })

    return {
        "exchange": selected_exchange,
        "interval": interval,
        "sourceStatus": "aggregated",
        "tickerStatus": "aggregated",
        "orderbookStatus": "aggregated",
        "symbolCount": len(pairs),
        "topSymbols": [p["key"] for p in pairs],
        "realTickerCount": 0,
        "realOrderbookCount": 0,
        "exchangeError": None,
        "exchangeSource": "sqlite_aggregation",
        "lastUpdate": now_iso(),
        "pairs": pairs,
    }
