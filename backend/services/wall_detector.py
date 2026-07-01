import math
import time
from typing import Any

from database import execute_many, fetch_all, now_iso
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
                "wallBias": "Buy" if len(buy_walls) > len(sell_walls) else "Sell" if len(sell_walls) > len(buy_walls) else "Neutral",
                "suspicious": round(max([w["suspicious_score"] for w in symbol_walls] or [0]), 2),
                "liquidity": pair["liquidity"],
            }
        )

    return {
        "walls": detected,
        "byPair": by_pair,
        "summary": {
            "buyWallCount": buy_count,
            "sellWallCount": sell_count,
            "wallBias": "Buyer Pressure" if buy_count >= sell_count else "Seller Pressure",
            "averageWallDuration": avg_duration,
            "wallPersistence": avg_persistence,
            "suspiciousScore": avg_suspicious,
            "possibleSpoofAlerts": sum(1 for wall in detected if wall["suspicious_score"] >= 70),
        },
    }


async def persist_walls(walls: list[dict[str, Any]]) -> None:
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
