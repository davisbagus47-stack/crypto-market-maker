import json
import math
import time
from typing import Any

from database import compute_window_cutoff, execute_many, fetch_all, now_iso
from services.settings_service import get_settings


def wall_score(size_usdt: float, duration_sec: int, spread_pct: float, side: str) -> float:
    size_component = min(42, math.log10(max(size_usdt, 1)) * 6)
    short_duration_component = max(0, 24 - duration_sec / 3)
    spread_component = min(18, spread_pct * 90)
    side_component = 6 if side == "sell" else 3
    return round(max(0, min(100, size_component + short_duration_component + spread_component + side_component)), 2)


def merge_nearby_walls(walls: list[dict[str, Any]], merge_pct: float = 0.002) -> list[dict[str, Any]]:
    if not walls:
        return []
    merged: list[dict[str, Any]] = []
    for wall in sorted(walls, key=lambda item: item["price"]):
        if not merged:
            merged.append(wall)
            continue
        previous = merged[-1]
        near = abs(wall["price"] - previous["price"]) / previous["price"] <= merge_pct
        if near and wall["side"] == previous["side"]:
            total_size = previous["size_usdt"] + wall["size_usdt"]
            previous["price"] = ((previous["price"] * previous["size_usdt"]) + (wall["price"] * wall["size_usdt"])) / total_size
            previous["quantity"] += wall["quantity"]
            previous["size_usdt"] = total_size
            previous["suspicious_score"] = max(previous["suspicious_score"], wall["suspicious_score"])
        else:
            merged.append(wall)
    return merged


def _build_wall_summary(pairs: list[dict[str, Any]], detected: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the standard wall summary dict from a list of detected walls and pair metadata."""
    buy_count = sum(1 for wall in detected if wall["side"] == "buy")
    sell_count = sum(1 for wall in detected if wall["side"] == "sell")
    avg_duration = round(sum(w["duration_sec"] for w in detected) / len(detected), 2) if detected else 0
    avg_persistence = round(sum(w["persistence_score"] for w in detected) / len(detected), 2) if detected else 0
    avg_suspicious = round(sum(w["suspicious_score"] for w in detected) / len(detected), 2) if detected else 0

    by_pair = []
    for pair in pairs:
        symbol_walls = [wall for wall in detected if wall["symbol"] == pair["key"]]
        buy_walls = [wall for wall in symbol_walls if wall["side"] == "buy"]
        sell_walls = [wall for wall in symbol_walls if wall["side"] == "sell"]
        by_pair.append(
            {
                "symbol": pair["displaySymbol"],
                "key": pair["key"],
                "buyWall": len(buy_walls),
                "sellWall": len(sell_walls),
                "buyWallSize": round(sum(w["size_usdt"] for w in buy_walls), 2),
                "sellWallSize": round(sum(w["size_usdt"] for w in sell_walls), 2),
                "wallBias": "Buyer Dominant" if len(buy_walls) > len(sell_walls) else "Seller Dominant" if len(sell_walls) > len(buy_walls) else "Balanced",
                "suspicious": round(max([w["suspicious_score"] for w in symbol_walls] or [0]), 2),
                "liquidity": pair.get("liquidity", 0),
            }
        )

    return {
        "walls": detected,
        "byPair": by_pair,
        "summary": {
            "buyWallCount": buy_count,
            "sellWallCount": sell_count,
            "wallBias": "Buyer Dominant" if buy_count > sell_count else "Seller Dominant" if sell_count > buy_count else "Balanced",
            "averageWallDuration": avg_duration,
            "wallPersistence": avg_persistence,
            "suspiciousScore": avg_suspicious,
            "possibleSpoofAlerts": sum(1 for wall in detected if wall["suspicious_score"] >= 70),
        },
    }


async def detect_walls(exchange: str, pairs: list[dict[str, Any]]) -> dict[str, Any]:
    settings = await get_settings()
    threshold = float(settings.get("minWallSize", 100000))
    detected: list[dict[str, Any]] = []
    timestamp = now_iso()
    for pair in pairs:
        symbol = pair["key"]
        for side, levels in (("buy", pair.get("bids", [])), ("sell", pair.get("asks", []))):
            raw_walls: list[dict[str, Any]] = []
            for price, qty in levels:
                size_usdt = float(price) * float(qty)
                if size_usdt >= threshold:
                    duration = int(18 + abs(math.sin(time.time() / 17 + price)) * 68)
                    raw_walls.append(
                        {
                            "timestamp": timestamp,
                            "exchange": exchange,
                            "symbol": symbol,
                            "displaySymbol": pair["displaySymbol"],
                            "side": side,
                            "wallType": "Buy Wall" if side == "buy" else "Sell Wall",
                            "price": round(float(price), 8),
                            "size_usdt": round(size_usdt, 2),
                            "quantity": round(float(qty), 8),
                            "duration_sec": duration,
                            "persistence_score": round(min(100, duration / 90 * 100), 2),
                            "suspicious_score": wall_score(size_usdt, duration, pair["spreadPct"], side),
                            "status": "active",
                        }
                    )
            detected.extend(merge_nearby_walls(raw_walls))

    await persist_walls(detected)
    return _build_wall_summary(pairs, detected)


# ---------------------------------------------------------------------------
# Timeframe-aware wall detection: queries historical orderbook snapshots
# and the walls table for walls within the selected time window.
# ---------------------------------------------------------------------------

async def detect_walls_for_interval(
    exchange: str,
    pairs: list[dict[str, Any]],
    interval: str,
) -> dict[str, Any]:
    """
    Detect walls aggregated over a time window.

    Strategy (two layers for maximum coverage):
      1. Query the ``walls`` table for walls already detected by the collector
         within the time window — this captures walls that were found in
         real-time by the background ``market_collector`` loop.
      2. Scan the latest ``orderbook_snapshots`` within the window and
         detect additional walls from the stored bid/ask levels.

    The result is merged and deduplicated, giving a timeframe-accurate
    wall count and bias for each pair.
    """
    settings = await get_settings()
    threshold = float(settings.get("minWallSize", 100000))
    cutoff = compute_window_cutoff(interval)
    symbols = [pair["key"] for pair in pairs]
    if not symbols:
        return _build_wall_summary(pairs, [])

    symbol_list = ",".join(f"'{s}'" for s in symbols)

    # ---- Layer 1: Historical walls from the ``walls`` table ----
    hist_query = f"""
        SELECT symbol, side, price, size_usdt, quantity, duration_sec,
               persistence_score, suspicious_score, timestamp
        FROM walls
        WHERE exchange = ?
          AND symbol IN ({symbol_list})
          AND timestamp >= ?
    """
    hist_rows = await fetch_all(hist_query, (exchange, cutoff))

    detected: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for row in hist_rows:
        # Deduplicate by (symbol, side, price rounded to 4 decimals)
        dedup_key = f"{row['symbol']}|{row['side']}|{round(float(row['price']), 4)}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)
        detected.append({
            "timestamp": row["timestamp"],
            "exchange": exchange,
            "symbol": row["symbol"],
            "displaySymbol": row["symbol"].replace("USDT", "/USDT"),
            "side": row["side"],
            "wallType": "Buy Wall" if row["side"] == "buy" else "Sell Wall",
            "price": round(float(row["price"]), 8),
            "size_usdt": round(float(row["size_usdt"]), 2),
            "quantity": round(float(row["quantity"]), 8),
            "duration_sec": int(row["duration_sec"]),
            "persistence_score": round(float(row["persistence_score"]), 2),
            "suspicious_score": round(float(row["suspicious_score"]), 2),
            "status": "historical",
        })

    # ---- Layer 2: Scan latest orderbook snapshots in the window ----
    # Get the most recent orderbook snapshot per symbol within the window
    book_query = f"""
        SELECT o.symbol, o.bids_json, o.asks_json, o.timestamp,
               m.spread_pct
        FROM orderbook_snapshots o
        LEFT JOIN market_snapshots m
            ON m.exchange = o.exchange AND m.symbol = o.symbol
               AND m.timestamp = o.timestamp
        WHERE o.exchange = ?
          AND o.symbol IN ({symbol_list})
          AND o.timestamp >= ?
        ORDER BY o.timestamp DESC
    """
    book_rows = await fetch_all(book_query, (exchange, cutoff))

    # Keep only the first (most recent) snapshot per symbol
    seen_symbols: set[str] = set()
    for row in book_rows:
        sym = row["symbol"]
        if sym in seen_symbols:
            continue
        seen_symbols.add(sym)

        spread_pct = float(row.get("spread_pct") or 0.005)
        display = sym.replace("USDT", "/USDT")
        for side, json_field in (("buy", row.get("bids_json", "[]")),
                                  ("sell", row.get("asks_json", "[]"))):
            try:
                levels = json.loads(json_field) if isinstance(json_field, str) else (json_field or [])
            except (json.JSONDecodeError, TypeError):
                levels = []
            raw_walls: list[dict[str, Any]] = []
            for level in levels:
                if not isinstance(level, (list, tuple)) or len(level) < 2:
                    continue
                price, qty = float(level[0]), float(level[1])
                size_usdt = price * qty
                if size_usdt >= threshold:
                    dedup_key = f"{sym}|{side}|{round(price, 4)}"
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)
                    duration = int(18 + abs(math.sin(time.time() / 17 + price)) * 68)
                    raw_walls.append({
                        "timestamp": row["timestamp"],
                        "exchange": exchange,
                        "symbol": sym,
                        "displaySymbol": display,
                        "side": side,
                        "wallType": "Buy Wall" if side == "buy" else "Sell Wall",
                        "price": round(price, 8),
                        "size_usdt": round(size_usdt, 2),
                        "quantity": round(qty, 8),
                        "duration_sec": duration,
                        "persistence_score": round(min(100, duration / 90 * 100), 2),
                        "suspicious_score": wall_score(size_usdt, duration, spread_pct, side),
                        "status": "snapshot_scan",
                    })
            detected.extend(merge_nearby_walls(raw_walls))

    # Do NOT persist here — historical walls were already persisted when
    # originally detected, and snapshot-scanned walls are ephemeral for
    # this view only.

    # Final merge of the combined detected list to handle any cross-layer
    # nearby walls that were not caught during per-batch merging.
    detected = merge_nearby_walls(detected)

    return _build_wall_summary(pairs, detected)


async def persist_walls(walls: list[dict[str, Any]]) -> None:
    if not walls:
        return
    rows = [
        (
            wall["timestamp"],
            wall["exchange"],
            wall["symbol"],
            wall["side"],
            wall["price"],
            wall["size_usdt"],
            wall["quantity"],
            wall["duration_sec"],
            wall["persistence_score"],
            wall["suspicious_score"],
            wall["status"],
            now_iso(),
        )
        for wall in walls
    ]
    await execute_many(
        """
        INSERT INTO walls (
            timestamp, exchange, symbol, side, price, size_usdt, quantity, duration_sec,
            persistence_score, suspicious_score, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


async def recent_walls(exchange: str, limit: int = 100) -> list[dict]:
    return await fetch_all(
        "SELECT * FROM walls WHERE exchange = ? ORDER BY id DESC LIMIT ?",
        (exchange, limit),
    )
import json
import math
import time
from typing import Any

from database import compute_window_cutoff, execute_many, fetch_all, now_iso
from services.settings_service import get_settings


def wall_score(size_usdt: float, duration_sec: int, spread_pct: float, side: str) -> float:
    size_component = min(42, math.log10(max(size_usdt, 1)) * 6)
    short_duration_component = max(0, 24 - duration_sec / 3)
    spread_component = min(18, spread_pct * 90)
    side_component = 6 if side == "sell" else 3
    return round(max(0, min(100, size_component + short_duration_component + spread_component + side_component)), 2)


def merge_nearby_walls(walls: list[dict[str, Any]], merge_pct: float = 0.002) -> list[dict[str, Any]]:
    if not walls:
        return []
    merged: list[dict[str, Any]] = []
    for wall in sorted(walls, key=lambda item: item["price"]):
        if not merged:
            merged.append(wall)
            continue
        previous = merged[-1]
        near = abs(wall["price"] - previous["price"]) / previous["price"] <= merge_pct
        if near and wall["side"] == previous["side"]:
            total_size = previous["size_usdt"] + wall["size_usdt"]
            previous["price"] = ((previous["price"] * previous["size_usdt"]) + (wall["price"] * wall["size_usdt"])) / total_size
            previous["quantity"] += wall["quantity"]
            previous["size_usdt"] = total_size
            previous["suspicious_score"] = max(previous["suspicious_score"], wall["suspicious_score"])
        else:
            merged.append(wall)
    return merged


def _build_wall_summary(pairs: list[dict[str, Any]], detected: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the standard wall summary dict from a list of detected walls and pair metadata."""
    buy_count = sum(1 for wall in detected if wall["side"] == "buy")
    sell_count = sum(1 for wall in detected if wall["side"] == "sell")
    avg_duration = round(sum(w["duration_sec"] for w in detected) / len(detected), 2) if detected else 0
    avg_persistence = round(sum(w["persistence_score"] for w in detected) / len(detected), 2) if detected else 0
    avg_suspicious = round(sum(w["suspicious_score"] for w in detected) / len(detected), 2) if detected else 0

    by_pair = []
    for pair in pairs:
        symbol_walls = [wall for wall in detected if wall["symbol"] == pair["key"]]
        buy_walls = [wall for wall in symbol_walls if wall["side"] == "buy"]
        sell_walls = [wall for wall in symbol_walls if wall["side"] == "sell"]
        by_pair.append(
            {
                "symbol": pair["displaySymbol"],
                "key": pair["key"],
                "buyWall": len(buy_walls),
                "sellWall": len(sell_walls),
                "buyWallSize": round(sum(w["size_usdt"] for w in buy_walls), 2),
                "sellWallSize": round(sum(w["size_usdt"] for w in sell_walls), 2),
                "wallBias": "Buyer Dominant" if len(buy_walls) > len(sell_walls) else "Seller Dominant" if len(sell_walls) > len(buy_walls) else "Balanced",
                "suspicious": round(max([w["suspicious_score"] for w in symbol_walls] or [0]), 2),
                "liquidity": pair.get("liquidity", 0),
            }
        )

    return {
        "walls": detected,
        "byPair": by_pair,
        "summary": {
            "buyWallCount": buy_count,
            "sellWallCount": sell_count,
            "wallBias": "Buyer Dominant" if buy_count > sell_count else "Seller Dominant" if sell_count > buy_count else "Balanced",
            "averageWallDuration": avg_duration,
            "wallPersistence": avg_persistence,
            "suspiciousScore": avg_suspicious,
            "possibleSpoofAlerts": sum(1 for wall in detected if wall["suspicious_score"] >= 70),
        },
    }


async def detect_walls(exchange: str, pairs: list[dict[str, Any]]) -> dict[str, Any]:
    settings = await get_settings()
    threshold = float(settings.get("minWallSize", 100000))
    detected: list[dict[str, Any]] = []
    timestamp = now_iso()
    for pair in pairs:
        symbol = pair["key"]
        for side, levels in (("buy", pair.get("bids", [])), ("sell", pair.get("asks", []))):
            raw_walls: list[dict[str, Any]] = []
            for price, qty in levels:
                size_usdt = float(price) * float(qty)
                if size_usdt >= threshold:
                    duration = int(18 + abs(math.sin(time.time() / 17 + price)) * 68)
                    raw_walls.append(
                        {
                            "timestamp": timestamp,
                            "exchange": exchange,
                            "symbol": symbol,
                            "displaySymbol": pair["displaySymbol"],
                            "side": side,
                            "wallType": "Buy Wall" if side == "buy" else "Sell Wall",
                            "price": round(float(price), 8),
                            "size_usdt": round(size_usdt, 2),
                            "quantity": round(float(qty), 8),
                            "duration_sec": duration,
                            "persistence_score": round(min(100, duration / 90 * 100), 2),
                            "suspicious_score": wall_score(size_usdt, duration, pair["spreadPct"], side),
                            "status": "active",
                        }
                    )
            detected.extend(merge_nearby_walls(raw_walls))

    await persist_walls(detected)
    return _build_wall_summary(pairs, detected)


# ---------------------------------------------------------------------------
# Timeframe-aware wall detection: queries historical orderbook snapshots
# and the walls table for walls within the selected time window.
# ---------------------------------------------------------------------------

async def detect_walls_for_interval(
    exchange: str,
    pairs: list[dict[str, Any]],
    interval: str,
) -> dict[str, Any]:
    """
    Detect walls aggregated over a time window.

    Strategy (two layers for maximum coverage):
      1. Query the ``walls`` table for walls already detected by the collector
         within the time window — this captures walls that were found in
         real-time by the background ``market_collector`` loop.
      2. Scan the latest ``orderbook_snapshots`` within the window and
         detect additional walls from the stored bid/ask levels.

    The result is merged and deduplicated, giving a timeframe-accurate
    wall count and bias for each pair.
    """
    settings = await get_settings()
    threshold = float(settings.get("minWallSize", 100000))
    cutoff = compute_window_cutoff(interval)
    symbols = [pair["key"] for pair in pairs]
    if not symbols:
        return _build_wall_summary(pairs, [])

    symbol_list = ",".join(f"'{s}'" for s in symbols)

    # ---- Layer 1: Historical walls from the ``walls`` table ----
    hist_query = f"""
        SELECT symbol, side, price, size_usdt, quantity, duration_sec,
               persistence_score, suspicious_score, timestamp
        FROM walls
        WHERE exchange = ?
          AND symbol IN ({symbol_list})
          AND timestamp >= ?
    """
    hist_rows = await fetch_all(hist_query, (exchange, cutoff))

    detected: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for row in hist_rows:
        # Deduplicate by (symbol, side, price rounded to 4 decimals)
        dedup_key = f"{row['symbol']}|{row['side']}|{round(float(row['price']), 4)}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)
        detected.append({
            "timestamp": row["timestamp"],
            "exchange": exchange,
            "symbol": row["symbol"],
            "displaySymbol": row["symbol"].replace("USDT", "/USDT"),
            "side": row["side"],
            "wallType": "Buy Wall" if row["side"] == "buy" else "Sell Wall",
            "price": round(float(row["price"]), 8),
            "size_usdt": round(float(row["size_usdt"]), 2),
            "quantity": round(float(row["quantity"]), 8),
            "duration_sec": int(row["duration_sec"]),
            "persistence_score": round(float(row["persistence_score"]), 2),
            "suspicious_score": round(float(row["suspicious_score"]), 2),
            "status": "historical",
        })

    # ---- Layer 2: Scan latest orderbook snapshots in the window ----
    # Get the most recent orderbook snapshot per symbol within the window
    book_query = f"""
        SELECT o.symbol, o.bids_json, o.asks_json, o.timestamp,
               m.spread_pct
        FROM orderbook_snapshots o
        LEFT JOIN market_snapshots m
            ON m.exchange = o.exchange AND m.symbol = o.symbol
               AND m.timestamp = o.timestamp
        WHERE o.exchange = ?
          AND o.symbol IN ({symbol_list})
          AND o.timestamp >= ?
        ORDER BY o.timestamp DESC
    """
    book_rows = await fetch_all(book_query, (exchange, cutoff))

    # Keep only the first (most recent) snapshot per symbol
    seen_symbols: set[str] = set()
    for row in book_rows:
        sym = row["symbol"]
        if sym in seen_symbols:
            continue
        seen_symbols.add(sym)

        spread_pct = float(row.get("spread_pct") or 0.005)
        display = sym.replace("USDT", "/USDT")
        for side, json_field in (("buy", row.get("bids_json", "[]")),
                                  ("sell", row.get("asks_json", "[]"))):
            try:
                levels = json.loads(json_field) if isinstance(json_field, str) else (json_field or [])
            except (json.JSONDecodeError, TypeError):
                levels = []
            raw_walls: list[dict[str, Any]] = []
            for level in levels:
                if not isinstance(level, (list, tuple)) or len(level) < 2:
                    continue
                price, qty = float(level[0]), float(level[1])
                size_usdt = price * qty
                if size_usdt >= threshold:
                    dedup_key = f"{sym}|{side}|{round(price, 4)}"
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)
                    duration = int(18 + abs(math.sin(time.time() / 17 + price)) * 68)
                    raw_walls.append({
                        "timestamp": row["timestamp"],
                        "exchange": exchange,
                        "symbol": sym,
                        "displaySymbol": display,
                        "side": side,
                        "wallType": "Buy Wall" if side == "buy" else "Sell Wall",
                        "price": round(price, 8),
                        "size_usdt": round(size_usdt, 2),
                        "quantity": round(qty, 8),
                        "duration_sec": duration,
                        "persistence_score": round(min(100, duration / 90 * 100), 2),
                        "suspicious_score": wall_score(size_usdt, duration, spread_pct, side),
                        "status": "snapshot_scan",
                    })
            detected.extend(merge_nearby_walls(raw_walls))

    # Do NOT persist here — historical walls were already persisted when
    # originally detected, and snapshot-scanned walls are ephemeral for
    # this view only.

    # Final merge of the combined detected list to handle any cross-layer
    # nearby walls that were not caught during per-batch merging.
    detected = merge_nearby_walls(detected)

    return _build_wall_summary(pairs, detected)


async def persist_walls(walls: list[dict[str, Any]]) -> None:
    if not walls:
        return
    rows = [
        (
            wall["timestamp"],
            wall["exchange"],
            wall["symbol"],
            wall["side"],
            wall["price"],
            wall["size_usdt"],
            wall["quantity"],
            wall["duration_sec"],
            wall["persistence_score"],
            wall["suspicious_score"],
            wall["status"],
            now_iso(),
        )
        for wall in walls
    ]
    await execute_many(
        """
        INSERT INTO walls (
            timestamp, exchange, symbol, side, price, size_usdt, quantity, duration_sec,
            persistence_score, suspicious_score, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


async def recent_walls(exchange: str, limit: int = 100) -> list[dict]:
    return await fetch_all(
        "SELECT * FROM walls WHERE exchange = ? ORDER BY id DESC LIMIT ?",
        (exchange, limit),
    )
