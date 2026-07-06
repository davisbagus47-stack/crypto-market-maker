def build_insights(pairs: list[dict], wall_summary: dict | None = None) -> list[dict]:
    if not pairs:
        return []
    avg_spread = sum(pair["spreadPct"] for pair in pairs) / len(pairs)
    avg_liquidity = sum(pair["liquidity"] for pair in pairs) / len(pairs)
    avg_slippage = sum(pair["slippage"] for pair in pairs) / len(pairs)
    total_imbalance = sum(pair["imbalance"] for pair in pairs)
    wall_summary = wall_summary or {}
    buy_walls = wall_summary.get("buyWallCount", 0)
    sell_walls = wall_summary.get("sellWallCount", 0)

    liquidity_title = "Healthy Liquidity" if avg_liquidity >= 70 and avg_spread < 0.05 else "Liquidity Needs Attention"
    liquidity_tone = "good" if avg_liquidity >= 70 else "warn" if avg_liquidity >= 50 else "bad"

    # Correct bias logic: positive imbalance = Buyer Dominant, negative = Seller Dominant
    # Wall counts are secondary signal; imbalance is the primary indicator
    if total_imbalance > 0.05:
        pressure_title = "Buyer Dominant"
        pressure_tone = "good"
        pressure_text = f"Order book imbalance is positive (+{total_imbalance:.4f}) — buy-side liquidity outweighs sell-side across selected markets."
    elif total_imbalance < -0.05:
        pressure_title = "Seller Dominant"
        pressure_tone = "warn"
        pressure_text = f"Order book imbalance is negative ({total_imbalance:.4f}) — sell-side liquidity outweighs buy-side across selected markets."
    else:
        # Near-neutral: use wall counts as tiebreaker
        if buy_walls > sell_walls:
            pressure_title = "Buyer Pressure"
            pressure_tone = "good"
        elif sell_walls > buy_walls:
            pressure_title = "Seller Pressure"
            pressure_tone = "warn"
        else:
            pressure_title = "Balanced"
            pressure_tone = "good"
        pressure_text = (
            f"Buy walls: {buy_walls}, Sell walls: {sell_walls} detected this interval. "
            "Order book is near equilibrium."
        )

    risk_pair = min(pairs, key=lambda pair: pair["liquidity"])
    slippage_title = "Low Slippage" if avg_slippage < 0.03 else "Elevated Slippage"

    return [
        {
            "label": "Overall Market",
            "title": liquidity_title,
            "tone": liquidity_tone,
            "text": "Spreads are tight and liquidity conditions are stable across major pairs."
            if liquidity_tone == "good"
            else "Liquidity conditions are uneven and should be monitored closely.",
        },
        {
            "label": "Buyer vs Seller",
            "title": pressure_title,
            "tone": pressure_tone,
            "text": pressure_text,
        },
        {
            "label": "Risk / Attention",
            "title": "Caution" if risk_pair["liquidity"] < 60 else "Stable",
            "tone": "warn" if risk_pair["liquidity"] < 60 else "good",
            "text": f"{risk_pair['displaySymbol']} has the weakest liquidity score in the selected group.",
        },
        {
            "label": "Slippage Outlook",
            "title": slippage_title,
            "tone": "good" if avg_slippage < 0.03 else "warn",
            "text": "Estimated slippage is low across major pairs under current conditions."
            if avg_slippage < 0.03
            else "Estimated slippage is increasing and may affect larger orders.",
        },
    ]
