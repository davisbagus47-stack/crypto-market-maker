from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DATA_DIR = BASE_DIR / "data"
GENERATED_REPORTS_DIR = BASE_DIR / "generated_reports"
DB_PATH = DATA_DIR / "market_data.db"

APP_NAME = "Crypto Liquidity Monitoring Dashboard"
TIMEZONE = "Asia/Jakarta"

DEFAULT_EXCHANGE = "Binance"
SUPPORTED_EXCHANGES = ["Binance", "Bybit", "OKX", "Gate.io", "Kraken", "MEXC"]
DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "BNBUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
]
FALLBACK_TOP_SYMBOLS = DEFAULT_SYMBOLS + [
    "LINKUSDT",
    "TRXUSDT",
    "POLUSDT",
    "DOTUSDT",
    "LTCUSDT",
    "BCHUSDT",
    "UNIUSDT",
    "AAVEUSDT",
    "ATOMUSDT",
    "NEARUSDT",
    "FILUSDT",
    "ETCUSDT",
]
SUPPORTED_INTERVALS = [
    "1s",
    "5s",
    "15s",
    "30s",
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "12h",
    "1D",
    "1W",
    "1M",
]

SYMBOL_DISPLAY = {
    "BTCUSDT": "BTC/USDT",
    "ETHUSDT": "ETH/USDT",
    "SOLUSDT": "SOL/USDT",
    "XRPUSDT": "XRP/USDT",
    "BNBUSDT": "BNB/USDT",
    "ADAUSDT": "ADA/USDT",
    "DOGEUSDT": "DOGE/USDT",
    "AVAXUSDT": "AVAX/USDT",
}

BASE_PRICES = {
    "BTCUSDT": 72923.87,
    "ETHUSDT": 3893.21,
    "SOLUSDT": 172.63,
    "XRPUSDT": 0.5289,
    "BNBUSDT": 612.18,
    "ADAUSDT": 0.4521,
    "DOGEUSDT": 0.1542,
    "AVAXUSDT": 35.12,
}

CORS_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

DEFAULT_SETTINGS = {
    "selectedExchange": "Binance",
    "primaryDataSource": "Binance REST API",
    "fallbackSource": "Local mock market generator",
    "autoRefresh": True,
    "refreshInterval": "5m",
    "maxSpreadThreshold": 0.5,
    "minWallSize": 100000,
    "imbalanceThreshold": 0.3,
    "lowLiquidityThreshold": 0.2,
    "suspiciousScoringSensitivity": 0.65,
    "notificationRules": {
        "enabled": True,
        "highSuspiciousScore": 70,
        "largeWallDetected": 100000,
        "highImbalance": 30,
        "lowLiquidity": 20,
    },
    "theme": "Dark",
    "accentColor": "blue",
    "exportPreferences": {
        "defaultFormat": "CSV",
        "includeCharts": True,
        "includeRawData": True,
        "compressExports": False,
    },
}


def parse_symbols(symbols: str | None) -> list[str]:
    if not symbols:
        return DEFAULT_SYMBOLS[:]
    parsed = [item.strip().upper().replace("/", "") for item in symbols.split(",") if item.strip()]
    return parsed or DEFAULT_SYMBOLS[:]


def normalize_exchange(exchange: str | None) -> str:
    if not exchange:
        return DEFAULT_EXCHANGE
    for supported in SUPPORTED_EXCHANGES:
        if supported.lower() == exchange.lower():
            return supported
    return exchange
