from fastapi import APIRouter, Query

from api.response import envelope
from config import parse_symbols
from database import interval_to_seconds
from services import alert_service, insight_service, market_service, wall_detector
from services.liquidity_service import liquidity_kpis

router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/overview")
async def overview(
    exchange: str = "Binance",
    symbols: str | None = Query(None),
    interval: str = "5m",
) -> dict:
    parsed_symbols = parse_symbols(symbols) if symbols else None
    use_aggregated = interval_to_seconds(interval) > 30

    if use_aggregated:
        market = await market_service.get_aggregated_market_data(exchange, parsed_symbols, interval)
        # Fallback: if aggregation returned no pairs (empty DB), fall back to real-time
        if not market.get("pairs"):
            market = await market_service.get_market_data(exchange, parsed_symbols, interval)
            use_aggregated = False

    if not use_aggregated:
        market = await market_service.get_market_data(exchange, parsed_symbols, interval)

    # Use timeframe-aware wall detection for aggregated intervals
    if use_aggregated:
        walls = await wall_detector.detect_walls_for_interval(
            market["exchange"], market["pairs"], interval
        )
    else:
        walls = await wall_detector.detect_walls(market["exchange"], market["pairs"])

    await alert_service.generate_alerts(market["exchange"], market["pairs"], walls["walls"])
    summary = await alert_service.alert_summary(market["exchange"])
    return envelope(
        source_status=market["sourceStatus"],
        exchange=market["exchange"],
        interval=interval,
        exchange_error=market.get("exchangeError"),
        data={
            "exchangeSource": market.get("exchangeSource"),
            "tickerStatus": market.get("tickerStatus"),
            "orderbookStatus": market.get("orderbookStatus"),
            "symbolCount": market.get("symbolCount"),
            "topSymbols": market.get("topSymbols"),
            "realTickerCount": market.get("realTickerCount"),
            "realOrderbookCount": market.get("realOrderbookCount"),
            "pairs": market["pairs"],
            "kpis": {
                **liquidity_kpis(market["pairs"]),
                **walls["summary"],
                "pairCount": len(market["pairs"]),
            },
            "walls": walls,
            "alerts": summary,
            "insights": insight_service.build_insights(market["pairs"], walls["summary"]),
        },
    )
from fastapi import APIRouter, Query

from api.response import envelope
from config import parse_symbols
from database import interval_to_seconds
from services import alert_service, insight_service, market_service, wall_detector
from services.liquidity_service import liquidity_kpis

router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/overview")
async def overview(
    exchange: str = "Binance",
    symbols: str | None = Query(None),
    interval: str = "5m",
) -> dict:
    parsed_symbols = parse_symbols(symbols) if symbols else None

    # Use aggregated (moving-window) query for intervals > 30s
    if interval_to_seconds(interval) > 30:
        market = await market_service.get_aggregated_market_data(exchange, parsed_symbols, interval)
    else:
        market = await market_service.get_market_data(exchange, parsed_symbols, interval)

    walls = await wall_detector.detect_walls(market["exchange"], market["pairs"])
    await alert_service.generate_alerts(market["exchange"], market["pairs"], walls["walls"])
    summary = await alert_service.alert_summary(market["exchange"])
    return envelope(
        source_status=market["sourceStatus"],
        exchange=market["exchange"],
        interval=interval,
        exchange_error=market.get("exchangeError"),
        data={
            "exchangeSource": market.get("exchangeSource"),
            "tickerStatus": market.get("tickerStatus"),
            "orderbookStatus": market.get("orderbookStatus"),
            "symbolCount": market.get("symbolCount"),
            "topSymbols": market.get("topSymbols"),
            "realTickerCount": market.get("realTickerCount"),
            "realOrderbookCount": market.get("realOrderbookCount"),
            "pairs": market["pairs"],
            "kpis": {
                **liquidity_kpis(market["pairs"]),
                **walls["summary"],
                "pairCount": len(market["pairs"]),
            },
            "walls": walls,
            "alerts": summary,
            "insights": insight_service.build_insights(market["pairs"], walls["summary"]),
        },
    )
