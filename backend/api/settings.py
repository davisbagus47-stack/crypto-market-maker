from fastapi import APIRouter

from api.response import envelope
from services.settings_service import get_settings, reset_settings, update_settings

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings")
async def settings() -> dict:
    data = await get_settings()
    return envelope(source_status="real", exchange=data.get("selectedExchange", "Binance"), data=data)


@router.put("/settings")
async def put_settings(updates: dict) -> dict:
    data = await update_settings(updates)
    return envelope(source_status="real", exchange=data.get("selectedExchange", "Binance"), data=data)


@router.post("/settings/reset")
async def reset() -> dict:
    data = await reset_settings()
    return envelope(source_status="real", exchange=data.get("selectedExchange", "Binance"), data=data)
