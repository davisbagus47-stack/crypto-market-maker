from fastapi import APIRouter, Query

from api.response import envelope
from config import parse_symbols
from database import classify_interval_tier
from services.market_service import get_aggregated_market_data, get_market_data

router = APIRouter(prefix="/api", tags=["markets"])


@router.get("/markets")
async def markets(
    exchange: str = "Binance",
    symbols: str | None = Query(None),
    interval: str = "5m",
) -> dict:
    parsed_symbols = parse_symbols(symbols) if symbols else None
    tier = classify_interval_tier(interval)
    use_aggregated = tier != "MICRO"

    if use_aggregated:
        market = await get_aggregated_market_data(exchange, parsed_symbols, interval)
        if not market.get("pairs"):
            market = await get_market_data(exchange, parsed_symbols, interval)
            use_aggregated = False

    if not use_aggregated:
        market = await get_market_data(exchange, parsed_symbols, interval)

    total_market_cap = sum(pair["marketCap"] for pair in market["pairs"]) * 1_000_000_000
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
            "summary": {
                "totalMarketCap": total_market_cap,
                "spotVolume24h": sum(pair["volume24h"] for pair in market["pairs"]),
                "futuresVolume24h": sum(pair["futuresVol"] for pair in market["pairs"]) * 1_000_000_000,
                "btcDominance": 61.32,
                "ethDominance": 9.37,
                "fearGreedIndex": 64,
            },
            "topMovers": sorted(market["pairs"], key=lambda pair: pair["change24h"], reverse=True),
        },
    )
