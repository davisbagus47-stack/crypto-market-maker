import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import aiosqlite

from config import DATA_DIR, DB_PATH, DEFAULT_SETTINGS, TIMEZONE


def now_iso() -> str:
    return datetime.now(ZoneInfo(TIMEZONE)).isoformat(timespec="seconds")


def interval_to_seconds(interval: str) -> int:
    """Convert interval string (e.g. '5m', '1h', '1D') to total seconds."""
    match = re.match(r"^(\d+)([smhDWM])$", interval, re.IGNORECASE)
    if not match:
        return 300  # default 5 minutes
    value = int(match.group(1))
    unit = match.group(2).upper()
    multipliers = {"S": 1, "M": 60, "H": 3600, "D": 86400, "W": 604800}
    if unit == "M" and value > 31:
        # Treat as months (~30 days each)
        return value * 30 * 86400
    return value * multipliers.get(unit, 60)


def compute_window_cutoff(interval: str) -> str:
    """Compute the cutoff timestamp (ISO) for a moving-window query, in the app timezone."""
    seconds = interval_to_seconds(interval)
    cutoff = datetime.now(ZoneInfo(TIMEZONE)) - timedelta(seconds=seconds)
    return cutoff.isoformat(timespec="seconds")


async def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                exchange TEXT,
                symbol TEXT,
                last_price REAL,
                best_bid REAL,
                best_ask REAL,
                bid_qty REAL,
                ask_qty REAL,
                spread REAL,
                spread_pct REAL,
                volume_24h REAL,
                change_24h REAL,
                funding_rate REAL,
                open_interest REAL,
                created_at TEXT
            )
            """
        )
        # Composite index for time-window aggregation queries
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_market_snapshots_exchange_symbol_ts
            ON market_snapshots (exchange, symbol, timestamp)
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS orderbook_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                exchange TEXT,
                symbol TEXT,
                bids_json TEXT,
                asks_json TEXT,
                bid_depth_top10 REAL,
                ask_depth_top10 REAL,
                imbalance REAL,
                slippage_100k REAL,
                liquidity_score REAL,
                created_at TEXT
            )
            """
        )
        # Index for time-window orderbook queries
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_orderbook_snapshots_exchange_symbol_ts
            ON orderbook_snapshots (exchange, symbol, timestamp)
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS walls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                exchange TEXT,
                symbol TEXT,
                side TEXT,
                price REAL,
                size_usdt REAL,
                quantity REAL,
                duration_sec INTEGER,
                persistence_score REAL,
                suspicious_score REAL,
                status TEXT,
                created_at TEXT
            )
            """
        )
        # Index for time-window wall queries
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_walls_exchange_symbol_ts
            ON walls (exchange, symbol, timestamp)
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange TEXT,
                timestamp TEXT,
                severity TEXT,
                symbol TEXT,
                alert_type TEXT,
                trigger_value TEXT,
                message TEXT,
                status TEXT,
                created_at TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                exchange TEXT,
                interval TEXT,
                summary_json TEXT,
                created_at TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                exchange TEXT,
                report_type TEXT,
                period TEXT,
                status TEXT,
                file_name TEXT,
                file_path TEXT,
                file_format TEXT,
                size_bytes INTEGER,
                created_at TEXT
            )
            """
        )
        await db.execute(
            """
            INSERT OR IGNORE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            """,
            ("app_settings", json.dumps(DEFAULT_SETTINGS), now_iso()),
        )
        await db.commit()


async def execute(query: str, params: tuple = ()) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(query, params)
        await db.commit()


async def execute_many(query: str, rows: list[tuple]) -> None:
    if not rows:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(query, rows)
        await db.commit()


async def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def fetch_one(query: str, params: tuple = ()) -> dict | None:
    rows = await fetch_all(query, params)
    return rows[0] if rows else None
