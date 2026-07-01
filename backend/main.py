import asyncio
import logging
from contextlib import suppress

from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import alerts, analytics, liquidity, markets, overview, reports, settings, walls
from config import APP_NAME, CORS_ORIGINS, FRONTEND_DIR
from database import init_db, now_iso
from services import alert_service, market_service, wall_detector
from services.settings_service import get_settings

app = FastAPI(title=APP_NAME)
collector_task: asyncio.Task | None = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_cache_frontend_assets(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith((".html", ".js", ".css")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

app.include_router(overview.router)
app.include_router(markets.router)
app.include_router(liquidity.router)
app.include_router(walls.router)
app.include_router(alerts.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(settings.router)


@app.get("/api/health")
async def health() -> dict:
    settings_data = await get_settings()
    exchange = settings_data.get("selectedExchange", "Binance")
    interval = settings_data.get("refreshInterval", "5m")
    probe = await market_service.get_market_data(exchange, ["BTCUSDT"], interval, persist=False)
    return {
        "status": "ok",
        "sourceStatus": probe["sourceStatus"],
        "exchange": probe["exchange"],
        "interval": interval,
        "lastUpdate": now_iso(),
        "exchangeError": probe.get("exchangeError"),
        "data": {
            "database": "ready",
            "frontend": FRONTEND_DIR.exists(),
            "collector": bool(collector_task and not collector_task.done()),
            "exchangeSource": probe.get("exchangeSource"),
            "btcPrice": probe["pairs"][0]["lastPrice"] if probe.get("pairs") else None,
        },
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


@app.get("/api/debug/binance")
async def debug_binance() -> dict:
    adapter = market_service.ADAPTERS["Binance"]
    debug = await adapter.debug_symbol("BTCUSDT")
    return {
        "status": "ok",
        "sourceStatus": "real" if debug["selectedSource"] != "fallback" else "fallback",
        "exchange": "Binance",
        "interval": None,
        "lastUpdate": now_iso(),
        "exchangeError": None if debug["selectedSource"] != "fallback" else debug.get("lastError"),
        "data": debug,
    }


@app.get("/api/debug/exchanges")
async def debug_exchanges(limit: int = Query(20, ge=1, le=20)) -> dict:
    rows = await market_service.debug_all_exchanges(limit=limit)
    source_status = "real" if all(row["sourceStatus"] == "real" for row in rows) else "partial_real" if any(row["sourceStatus"] != "fallback" for row in rows) else "fallback"
    return {
        "status": "ok",
        "sourceStatus": source_status,
        "exchange": "all",
        "interval": None,
        "lastUpdate": now_iso(),
        "exchangeError": None,
        "data": rows,
    }


@app.get("/api/debug/exchange")
async def debug_exchange(exchange: str = "Binance", limit: int = Query(20, ge=1, le=20)) -> dict:
    row = await market_service.debug_exchange(exchange, limit=limit)
    return {
        "status": "ok",
        "sourceStatus": row["sourceStatus"],
        "exchange": row["exchange"],
        "interval": None,
        "lastUpdate": now_iso(),
        "exchangeError": row.get("lastError"),
        "data": row,
    }


async def market_collector() -> None:
    while True:
        try:
            settings_data = await get_settings()
            exchange = settings_data.get("selectedExchange", "Binance")
            interval = settings_data.get("refreshInterval", "5m")
            market = await market_service.get_market_data(exchange, None, interval, persist=True)
            wall_data = await wall_detector.detect_walls(market["exchange"], market["pairs"])
            await alert_service.generate_alerts(market["exchange"], market["pairs"], wall_data["walls"])
        except Exception:
            # Collector should never bring down the dashboard. Endpoints have their own fallback path.
            pass
        await asyncio.sleep(15)


@app.on_event("startup")
async def on_startup() -> None:
    global collector_task
    await init_db()
    await get_settings()
    collector_task = asyncio.create_task(market_collector())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if collector_task:
        collector_task.cancel()
        with suppress(asyncio.CancelledError):
            await collector_task


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
