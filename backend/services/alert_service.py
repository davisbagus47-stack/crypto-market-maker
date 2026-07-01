from typing import Any

from database import execute, fetch_all, fetch_one, now_iso
from services.settings_service import get_settings


async def create_alert(
    exchange: str,
    severity: str,
    symbol: str,
    alert_type: str,
    trigger_value: str,
    message: str,
) -> None:
    recent = await fetch_one(
        """
        SELECT id FROM alerts
        WHERE exchange = ? AND symbol = ? AND alert_type = ? AND status != 'Resolved'
        ORDER BY id DESC LIMIT 1
        """,
        (exchange, symbol, alert_type),
    )
    if recent:
        return
    timestamp = now_iso()
    await execute(
        """
        INSERT INTO alerts (
            exchange, timestamp, severity, symbol, alert_type, trigger_value, message, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (exchange, timestamp, severity, symbol, alert_type, trigger_value, message, "Unacknowledged", timestamp),
    )


async def generate_alerts(exchange: str, pairs: list[dict[str, Any]], walls: list[dict[str, Any]] | None = None) -> None:
    settings = await get_settings()
    max_spread = float(settings.get("maxSpreadThreshold", 0.5))
    imbalance_threshold = float(settings.get("imbalanceThreshold", 0.3))
    low_liquidity_score = float(settings.get("lowLiquidityThreshold", 0.2)) * 100
    min_wall_size = float(settings.get("minWallSize", 100000))
    suspicious_threshold = float(settings.get("notificationRules", {}).get("highSuspiciousScore", 70))

    for pair in pairs:
        symbol = pair["key"]
        if pair["spreadPct"] > max_spread:
            await create_alert(
                exchange,
                "CRITICAL",
                symbol,
                "Spread Spike",
                f"{pair['spreadPct']:.4f}%",
                f"{pair['displaySymbol']} spread exceeded configured threshold.",
            )
        if abs(pair["imbalance"]) >= imbalance_threshold:
            await create_alert(
                exchange,
                "WARNING",
                symbol,
                "Order Book Imbalance",
                f"{pair['imbalance']:.4f}",
                f"{pair['displaySymbol']} order book imbalance is elevated.",
            )
        if pair["liquidity"] < low_liquidity_score:
            await create_alert(
                exchange,
                "WARNING",
                symbol,
                "Low Liquidity",
                f"{pair['liquidity']:.1f}",
                f"{pair['displaySymbol']} liquidity score is below threshold.",
            )
        if pair.get("slippage", 0) > 0.05:
            await create_alert(
                exchange,
                "WARNING",
                symbol,
                "Liquidity Deterioration",
                f"{pair['slippage']:.4f}%",
                f"{pair['displaySymbol']} slippage estimate is deteriorating.",
            )

    for wall in walls or []:
        if wall["size_usdt"] >= min_wall_size:
            await create_alert(
                exchange,
                "INFO",
                wall["symbol"],
                "Large Wall Detected",
                f"{wall['size_usdt']:.0f} USDT",
                f"{wall['displaySymbol']} has a large {wall['side']} wall.",
            )
        if wall["suspicious_score"] >= suspicious_threshold:
            await create_alert(
                exchange,
                "WARNING",
                wall["symbol"],
                "Suspicious Wall",
                f"{wall['suspicious_score']:.0f}",
                f"{wall['displaySymbol']} wall behavior is suspicious.",
            )


async def get_alerts(
    exchange: str,
    severity: str = "all",
    status: str = "all",
    alert_type: str = "all",
    search: str = "",
    limit: int = 100,
) -> list[dict]:
    conditions = ["exchange = ?"]
    params: list[Any] = [exchange]
    if severity and severity.lower() != "all":
        conditions.append("LOWER(severity) = LOWER(?)")
        params.append(severity)
    if status and status.lower() != "all":
        conditions.append("LOWER(status) = LOWER(?)")
        params.append(status)
    if alert_type and alert_type.lower() != "all":
        conditions.append("LOWER(alert_type) = LOWER(?)")
        params.append(alert_type)
    if search:
        conditions.append("(LOWER(symbol) LIKE LOWER(?) OR LOWER(message) LIKE LOWER(?) OR LOWER(alert_type) LIKE LOWER(?))")
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern])
    params.append(limit)
    return await fetch_all(
        f"SELECT * FROM alerts WHERE {' AND '.join(conditions)} ORDER BY id DESC LIMIT ?",
        tuple(params),
    )


async def alert_summary(exchange: str) -> dict:
    rows = await fetch_all("SELECT severity, status FROM alerts WHERE exchange = ?", (exchange,))
    return {
        "critical": sum(1 for row in rows if row["severity"].upper() == "CRITICAL"),
        "warning": sum(1 for row in rows if row["severity"].upper() == "WARNING"),
        "info": sum(1 for row in rows if row["severity"].upper() == "INFO"),
        "unacknowledged": sum(1 for row in rows if row["status"] == "Unacknowledged"),
        "acknowledged": sum(1 for row in rows if row["status"] == "Acknowledged"),
        "total": len(rows),
    }
