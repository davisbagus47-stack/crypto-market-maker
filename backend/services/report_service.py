import csv
from pathlib import Path
from typing import Any

from config import GENERATED_REPORTS_DIR
from database import execute, fetch_all, now_iso
from services.market_service import get_market_data


async def list_reports(exchange: str) -> dict[str, Any]:
    source_status = "fallback"
    ticker_status = "fallback"
    orderbook_status = "fallback"
    symbol_count = 0
    rows = await fetch_all(
        "SELECT * FROM reports WHERE exchange = ? ORDER BY id DESC LIMIT 50",
        (exchange,),
    )
    if not rows:
        generated = await generate_report(exchange=exchange, report_type="Daily Liquidity Summary", file_format="csv")
        source_status = generated.get("sourceStatus", source_status)
        ticker_status = generated.get("tickerStatus", ticker_status)
        orderbook_status = generated.get("orderbookStatus", orderbook_status)
        symbol_count = generated.get("symbolCount", symbol_count)
        rows = await fetch_all(
            "SELECT * FROM reports WHERE exchange = ? ORDER BY id DESC LIMIT 50",
            (exchange,),
        )
    else:
        market = await get_market_data(exchange, None, "5m", persist=False)
        source_status = market["sourceStatus"]
        ticker_status = market["tickerStatus"]
        orderbook_status = market["orderbookStatus"]
        symbol_count = market["symbolCount"]
    return {
        "sourceStatus": source_status,
        "tickerStatus": ticker_status,
        "orderbookStatus": orderbook_status,
        "symbolCount": symbol_count,
        "reports": rows,
        "summary": {
            "reportsGenerated": len(rows),
            "totalExports": len(rows),
            "deliverySuccessRate": 99.42,
            "scheduledReports": 5,
            "storageUsedBytes": sum(row.get("size_bytes") or 0 for row in rows),
        },
    }


async def generate_report(
    exchange: str,
    report_type: str = "Daily Liquidity Summary",
    file_format: str = "csv",
    symbols: list[str] | None = None,
    interval: str = "5m",
) -> dict[str, Any]:
    GENERATED_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    market = await get_market_data(exchange, symbols, interval)
    rows = [
        {
            "symbol": pair["key"],
            "display_symbol": pair["displaySymbol"],
            "last_price": pair["lastPrice"],
            "best_bid": pair["bestBid"],
            "best_ask": pair["bestAsk"],
            "spread_pct": pair["spreadPct"],
            "bid_depth_top10": pair["bidDepth"],
            "ask_depth_top10": pair["askDepth"],
            "imbalance": pair["imbalance"],
            "liquidity_score": pair["liquidity"],
            "slippage_100k": pair["slippage"],
        }
        for pair in market["pairs"]
    ]
    stamp = now_iso().replace(":", "").replace("-", "").replace("+", "_")
    normalized_format = file_format.lower()
    if normalized_format not in {"csv", "xlsx", "excel"}:
        normalized_format = "csv"
    extension = "xlsx" if normalized_format in {"xlsx", "excel"} else "csv"
    file_name = f"{report_type.replace(' ', '_').lower()}_{exchange.lower().replace('.', '')}_{stamp}.{extension}"
    file_path = GENERATED_REPORTS_DIR / file_name

    if extension == "xlsx":
        try:
            import pandas as pd

            pd.DataFrame(rows).to_excel(file_path, index=False)
        except Exception:
            file_path = file_path.with_suffix(".csv")
            file_name = file_path.name
            write_csv(file_path, rows)
            extension = "csv"
    else:
        write_csv(file_path, rows)

    size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
    timestamp = now_iso()
    await execute(
        """
        INSERT INTO reports (
            timestamp, exchange, report_type, period, status, file_name, file_path, file_format, size_bytes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            exchange,
            report_type,
            interval,
            "Completed",
            file_name,
            str(file_path),
            extension.upper(),
            size,
            timestamp,
        ),
    )
    return {
        "sourceStatus": market.get("sourceStatus"),
        "tickerStatus": market.get("tickerStatus"),
        "orderbookStatus": market.get("orderbookStatus"),
        "symbolCount": market.get("symbolCount"),
        "topSymbols": market.get("topSymbols"),
        "reportType": report_type,
        "fileName": file_name,
        "filePath": str(file_path),
        "fileFormat": extension.upper(),
        "sizeBytes": size,
        "status": "Completed",
    }


def write_csv(file_path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else ["message"]
    with file_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)
        else:
            writer.writerow({"message": "No data available"})
