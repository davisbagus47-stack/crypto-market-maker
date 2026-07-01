from fastapi import APIRouter, Query

from api.response import envelope
from config import parse_symbols
from services import alert_service, market_service, wall_detector

router = APIRouter(prefix="/api", tags=["walls"])


@router.get("/walls")
async def walls(
    exchange: str = "Binance",
    symbols: str | None = Query(None),
    interval: str = "5m",
) -> dict:
    market = await market_service.get_market_data(exchange, parse_symbols(symbols) if symbols else None, interval)
    wall_data = await wall_detector.detect_walls(market["exchange"], market["pairs"])
    await alert_service.generate_alerts(market["exchange"], market["pairs"], wall_data["walls"])
    return envelope(
        source_status=market["sourceStatus"],
        exchange=market["exchange"],
        interval=interval,
        exchange_error=market.get("exchangeError"),
        data={
            **wall_data,
            "exchangeSource": market.get("exchangeSource"),
            "tickerStatus": market.get("tickerStatus"),
            "orderbookStatus": market.get("orderbookStatus"),
            "symbolCount": market.get("symbolCount"),
            "topSymbols": market.get("topSymbols"),
            "realTickerCount": market.get("realTickerCount"),
            "realOrderbookCount": market.get("realOrderbookCount"),
            "pairs": market["pairs"],
        },
    )
