from fastapi import APIRouter, Query

from api.response import envelope
from config import parse_symbols
from services.liquidity_service import get_liquidity

router = APIRouter(prefix="/api", tags=["liquidity"])


@router.get("/liquidity")
async def liquidity(
    exchange: str = "Binance",
    symbols: str | None = Query(None),
    interval: str = "5m",
) -> dict:
    data = await get_liquidity(exchange, parse_symbols(symbols) if symbols else None, interval)
    return envelope(
        source_status=data["sourceStatus"],
        exchange=data["exchange"],
        interval=interval,
        exchange_error=data.get("exchangeError"),
        data=data,
    )
