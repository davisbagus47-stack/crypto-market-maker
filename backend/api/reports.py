from pydantic import BaseModel
from fastapi import APIRouter

from api.response import envelope
from config import parse_symbols
from services.report_service import generate_report, list_reports

router = APIRouter(prefix="/api", tags=["reports"])


class ReportRequest(BaseModel):
    exchange: str = "Binance"
    reportType: str = "Daily Liquidity Summary"
    fileFormat: str = "csv"
    symbols: str | None = None
    interval: str = "5m"


@router.get("/reports")
async def reports(exchange: str = "Binance") -> dict:
    data = await list_reports(exchange)
    return envelope(
        source_status=data.get("sourceStatus", "fallback"),
        exchange=exchange,
        exchange_error=None,
        data=data,
    )


@router.post("/reports/generate")
async def generate(request: ReportRequest) -> dict:
    data = await generate_report(
        exchange=request.exchange,
        report_type=request.reportType,
        file_format=request.fileFormat,
        symbols=parse_symbols(request.symbols) if request.symbols else None,
        interval=request.interval,
    )
    return envelope(
        source_status=data.get("sourceStatus", "fallback"),
        exchange=request.exchange,
        interval=request.interval,
        data=data,
    )
