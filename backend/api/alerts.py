from fastapi import APIRouter

from api.response import envelope
from services import alert_service, market_service, wall_detector

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts")
async def alerts(
    exchange: str = "Binance",
    severity: str = "all",
    status: str = "all",
    type: str = "all",
    search: str = "",
) -> dict:
    market = await market_service.get_market_data(exchange, None, "5m")
    walls = await wall_detector.detect_walls(market["exchange"], market["pairs"])
    await alert_service.generate_alerts(market["exchange"], market["pairs"], walls["walls"])
    rows = await alert_service.get_alerts(market["exchange"], severity, status, type, search)
    summary = await alert_service.alert_summary(market["exchange"])
    return envelope(
        source_status=market["sourceStatus"],
        exchange=market["exchange"],
        interval="5m",
        exchange_error=market.get("exchangeError"),
        data={
            "exchangeSource": market.get("exchangeSource"),
            "tickerStatus": market.get("tickerStatus"),
            "orderbookStatus": market.get("orderbookStatus"),
            "symbolCount": market.get("symbolCount"),
            "topSymbols": market.get("topSymbols"),
            "realTickerCount": market.get("realTickerCount"),
            "realOrderbookCount": market.get("realOrderbookCount"),
            "alerts": rows,
            "summary": summary,
        },
    )
