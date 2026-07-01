from fastapi import APIRouter, Query

from api.response import envelope
from config import parse_symbols
from services.analytics_service import get_analytics

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics")
async def analytics(
    exchange: str = "Binance",
    symbols: str | None = Query(None),
    interval: str = "5m",
) -> dict:
    data = await get_analytics(exchange, parse_symbols(symbols) if symbols else None, interval)
    return envelope(
        source_status=data["sourceStatus"],
        exchange=data["exchange"],
        interval=interval,
        exchange_error=data.get("exchangeError"),
        data=data,
    )
