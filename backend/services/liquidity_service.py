from database import classify_interval_tier
from services.market_service import get_aggregated_market_data, get_market_data


def liquidity_kpis(pairs: list[dict]) -> dict:
    if not pairs:
        return {}
    return {
        "averageSpread": round(sum(pair["spreadPct"] for pair in pairs) / len(pairs), 6),
        "maxSpread": round(max(pair["spreadPct"] for pair in pairs), 6),
        "bidDepthTop10": round(sum(pair["bidDepth"] for pair in pairs), 2),
        "askDepthTop10": round(sum(pair["askDepth"] for pair in pairs), 2),
        "topOfBookDepth": round(sum(pair["bestBid"] * pair["bidQty"] + pair["bestAsk"] * pair["askQty"] for pair in pairs), 2),
        "slippageEstimate": round(sum(pair["slippage"] for pair in pairs) / len(pairs), 6),
        "liquidityScore": round(sum(pair["liquidity"] for pair in pairs) / len(pairs), 2),
        "orderBookResilience": round(sum(pair["resilience"] for pair in pairs) / len(pairs), 4),
    }


async def get_liquidity(exchange: str, symbols: list[str] | None, interval: str) -> dict:
    tier = classify_interval_tier(interval)
    use_aggregated = tier != "MICRO"

    if use_aggregated:
        market = await get_aggregated_market_data(exchange, symbols, interval)
        if not market.get("pairs"):
            market = await get_market_data(exchange, symbols, interval)
            use_aggregated = False

    if not use_aggregated:
        market = await get_market_data(exchange, symbols, interval)

    pairs = market["pairs"]
    return {
        **market,
        "kpis": liquidity_kpis(pairs),
        "comparison": [
            {
                "symbol": pair["displaySymbol"],
                "spreadPct": pair["spreadPct"],
                "totalDepth": round(pair["bidDepth"] + pair["askDepth"], 2),
                "liquidityScore": pair["liquidity"],
            }
            for pair in pairs
        ],
        "slippageCurve": [
            {"orderSize": size, "slippage": round((size / 100000) * (sum(p["slippage"] for p in pairs) / len(pairs)), 6)}
            for size in [10000, 50000, 100000, 500000, 1000000, 5000000]
        ],
    }
