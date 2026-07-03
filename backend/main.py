import asyncio
import json
import logging
from contextlib import suppress

from fastapi import FastAPI, Query, Response, WebSocket, WebSocketDisconnect
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
logger = logging.getLogger("ws")


class ConnectionManager:
    """Melacak koneksi WebSocket yang aktif dan melakukan broadcast payload JSON ke semuanya."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info("WebSocket connected. Total active: %d", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected. Total active: %d", len(self.active_connections))

    async def broadcast(self, message: dict) -> None:
        if not self.active_connections:
            return
        payload = json.dumps(message, default=str)
        async with self._lock:
            connections = list(self.active_connections)
        stale: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_text(payload)
            except Exception:
                stale.append(connection)
        if stale:
            async with self._lock:
                for connection in stale:
                    if connection in self.active_connections:
                        self.active_connections.remove(connection)


manager = ConnectionManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            # Dashboard ini bersifat server-push (broadcast-only), tapi kita tetap
            # menunggu frame masuk supaya disconnect dari sisi client terdeteksi
            # (recv akan raise WebSocketDisconnect saat koneksi ditutup/putus).
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)


async def market_collector() -> None:
    while True:
        try:
            settings_data = await get_settings()
            exchange = settings_data.get("selectedExchange", "Binance")
            interval = settings_data.get("refreshInterval", "5m")
            market = await market_service.get_market_data(exchange, None, interval, persist=True)
            wall_data = await wall_detector.detect_walls(market["exchange"], market["pairs"])
            alert_list = await alert_service.generate_alerts(market["exchange"], market["pairs"], wall_data["walls"])

            # Broadcast hasil tick ini ke semua client WebSocket yang aktif.
            # Envelope-nya sengaja disamakan dengan response HTTP endpoint yang sudah
            # ada (status/sourceStatus/exchange/interval/lastUpdate/exchangeError/data)
            # supaya bisa langsung dikonsumsi oleh applyBackendData() di frontend.
            #
            # PENTING: `market["pairs"]` dan `wall_data` di sini adalah bentuk MENTAH
            # dari service layer (persis yang dipakai untuk persist ke DB di atas) —
            # BUKAN bentuk hasil reshape yang biasa dikembalikan oleh endpoint
            # /api/overview (field kpis, insights, walls.summary/byPair, dsb). Karena
            # file reshape itu (api/overview.py & service terkait) tidak ada di
            # konteks saat ini, field-field agregat tersebut TIDAK diisi ulang di sini
            # agar tidak menimpa data yang sudah benar dari fetch awal. Ganti bagian
            # "data" di bawah ini dengan pemanggilan fungsi reshape yang sama dengan
            # yang dipakai overview.router agar kpis/insights/walls ikut live juga.
            await manager.broadcast({
                "status": "ok",
                "sourceStatus": market.get("sourceStatus"),
                "exchange": market.get("exchange"),
                "interval": interval,
                "lastUpdate": now_iso(),
                "exchangeError": market.get("exchangeError"),
                "data": {
                    "pairs": market.get("pairs", []),
                    "walls": wall_data,
                    "alerts": alert_list,
                },
            })
        except Exception:
            # Collector should never bring down the dashboard. Endpoints have their own fallback path.
            logger.exception("market_collector tick failed")
        await asyncio.sleep(1)


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