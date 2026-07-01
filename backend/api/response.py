from typing import Any

from database import now_iso


def envelope(
    *,
    source_status: str = "fallback",
    exchange: str = "Binance",
    interval: str | None = None,
    exchange_error: str | None = None,
    data: Any = None,
) -> dict:
    return {
        "status": "ok",
        "sourceStatus": source_status,
        "exchange": exchange,
        "interval": interval,
        "lastUpdate": now_iso(),
        "exchangeError": exchange_error,
        "data": data if data is not None else {},
    }
