from fastapi import APIRouter, Query

from api.response import envelope
from config import parse_symbols
from database import interval_to_seconds
from services import alert_service, market_service, wall_detector

router = APIRouter(prefix="/api", tags=["walls"])


@router.get("/walls")
async def walls(
    exchange: str = "Binance",
    symbols: str | None = Query(None),
    interval: str = "5m",
) -> dict:
    parsed_symbols = parse_symbols(symbols) if symbols else None
    use_aggregated = interval_to_seconds(interval) > 30

    if use_aggregated:
        market = await market_service.get_aggregated_market_data(exchange, parsed_symbols, interval)
        if not market.get("pairs"):
            market = await market_service.get_market_data(exchange, parsed_symbols, interval)
            use_aggregated = False

    if not use_aggregated:
        market = await market_service.get_market_data(exchange, parsed_symbols, interval)

    # Use timeframe-aware wall detection for aggregated intervals
    if use_aggregated:
        wall_data = await wall_detector.detect_walls_for_interval(
            market["exchange"], market["pairs"], interval
        )
    else:
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
from fastapi import APIRouter, Query

from api.response import envelope
from config import parse_symbols
from database import interval_to_seconds
from services import alert_service, market_service, wall_detector

router = APIRouter(prefix="/api", tags=["walls"])


@router.get("/walls")
async def walls(
    exchange: str = "Binance",
    symbols: str | None = Query(None),
    interval: str = "5m",
) -> dict:
    parsed_symbols = parse_symbols(symbols) if symbols else None
    if interval_to_seconds(interval) > 30:
        market = await market_service.get_aggregated_market_data(exchange, parsed_symbols, interval)
    else:
        market = await market_service.get_market_data(exchange, parsed_symbols, interval)
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
