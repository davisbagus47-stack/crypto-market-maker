const state = {
  page: "overview",
  exchange: "Binance",
  symbolGroup: "Major Pairs",
  timeframe: "5m",
  timeframeMenuOpen: false,
  overviewPage: 1,
  overviewPageSize: 5,
  autoRefresh: true,
  lastUpdate: new Date(),
  selectedPair: "BTC/USDT",
  topMoverTab: "gainers",
  futuresTab: "24H",
  reportTab: "pnl",
  // Live data from backend
  kpis: {},
  wallSummary: {},
  marketSummary: {},
  liquidityComparison: [],
  slippageCurve: [],
  insights: [],
  sourceStatus: "unknown",
  alertFilters: {
    severity: "All Severities",
    status: "All Statuses",
    type: "All Types",
    search: ""
  },
  settings: {
    refresh: true,
    reconnect: true,
    wallCharts: true,
    wallTags: true,
    notifications: true,
    compactMode: false,
    animations: true,
    includeCharts: true,
    includeRaw: true,
    compressExports: true,
    accent: "blue"
  }
};

const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://127.0.0.1:8000/api"
  : "https://crypto-market-maker-production.up.railway.app/api";
let backendWarningShown = false;
let socket = null;
let wsReconnectTimer = null;

const navItems = [
  ["overview", "Overview", "grid"],
  ["markets", "Markets", "trend"],
  ["liquidity", "Liquidity", "droplet"],
  ["walls", "Walls", "layers"],
  ["alerts", "Alerts", "bell"],
  ["analytics", "Analytics", "chart"],
  ["reports", "Reports", "file"],
  ["settings", "Settings", "settings"]
];

const timeframeGroups = [
  { title: "Seconds", items: ["1s", "5s", "15s", "30s"] },
  { title: "Minutes", items: ["1m", "5m", "15m", "30m"] },
  { title: "Hours", items: ["1h", "4h", "12h"] },
  { title: "Days", items: ["1D", "1W", "1M"] }
];

const favoriteTimeframes = ["1s", "1m", "5m", "15m", "1h", "4h", "1D"];

const palette = {
  blue: "#2d8cff",
  cyan: "#21d4e8",
  green: "#31d06b",
  red: "#ff4d4f",
  amber: "#ffbd2e",
  violet: "#9a6bff",
  magenta: "#ec6ce8",
  orange: "#ff8d2d",
  muted: "#71879e"
};

const tokenLogos = {
  BTC: ["BT", "linear-gradient(145deg, #ffad33, #f07800)", "#111"],
  ETH: ["ET", "linear-gradient(145deg, #9e98ff, #5d61e8)", "#fff"],
  SOL: ["SO", "linear-gradient(145deg, #37f2b1, #7a4dff)", "#061522"],
  XRP: ["XR", "linear-gradient(145deg, #1b2635, #05080d)", "#fff"],
  BNB: ["BN", "linear-gradient(145deg, #ffda52, #e7a800)", "#111"],
  ADA: ["AD", "linear-gradient(145deg, #2f9dff, #0d56bd)", "#fff"],
  DOGE: ["DO", "linear-gradient(145deg, #f8d96c, #c79d21)", "#111"],
  AVAX: ["AV", "linear-gradient(145deg, #ff686b, #db2529)", "#fff"],
  USDC: ["US", "linear-gradient(145deg, #4fa7ff, #2167d8)", "#fff"],
  USD1: ["U1", "linear-gradient(145deg, #f7fbff, #8da2bb)", "#071625"],
  USDE: ["UD", "linear-gradient(145deg, #d6fff7, #2cc5b6)", "#06201d"],
  WLD: ["WL", "linear-gradient(145deg, #222b3a, #05080d)", "#fff"],
  HYPE: ["HY", "linear-gradient(145deg, #7df7d4, #09a98b)", "#041a16"],
  ZEC: ["ZE", "linear-gradient(145deg, #f5c94a, #a86d15)", "#111"],
  XAUT: ["XA", "linear-gradient(145deg, #ffd66b, #a87311)", "#111"],
  BABY: ["BA", "linear-gradient(145deg, #ff9bc5, #b94184)", "#fff"],
  NEAR: ["NE", "linear-gradient(145deg, #f3fff8, #7fd8ac)", "#071712"],
  UNI: ["UN", "linear-gradient(145deg, #ff75d6, #c12e91)", "#fff"],
  SPXCB: ["SP", "linear-gradient(145deg, #ff7e54, #b72d18)", "#fff"],
  TAO: ["TA", "linear-gradient(145deg, #a7f0ff, #2779d8)", "#061522"],
  XLM: ["XL", "linear-gradient(145deg, #d7e2ef, #5a6c83)", "#071625"],
  SUI: ["SU", "linear-gradient(145deg, #68d6ff, #1f7ed9)", "#fff"],
  TRX: ["TR", "linear-gradient(145deg, #ff4d5f, #a70f1d)", "#fff"],
  LINK: ["LI", "linear-gradient(145deg, #5d8cff, #2252c7)", "#fff"],
  POL: ["PO", "linear-gradient(145deg, #a877ff, #5e2bc9)", "#fff"],
  DOT: ["DO", "linear-gradient(145deg, #ff6abc, #b31e76)", "#fff"],
  LTC: ["LT", "linear-gradient(145deg, #d8e1ef, #66758b)", "#071625"],
  BCH: ["BC", "linear-gradient(145deg, #72dd88, #228844)", "#071b0c"],
  AAVE: ["AA", "linear-gradient(145deg, #b586ff, #36d3c4)", "#fff"],
  ATOM: ["AT", "linear-gradient(145deg, #7f8cff, #262d66)", "#fff"],
  FIL: ["FI", "linear-gradient(145deg, #5de4ff, #1686a8)", "#061522"],
  ETC: ["EC", "linear-gradient(145deg, #4ed16f, #126d32)", "#fff"]
};

const tokenLogoAliases = {
  SPXCB: "SPX"
};

const tokenLogoImages = {
  BTC: "https://coin-images.coingecko.com/coins/images/1/large/bitcoin.png?1696501400",
  ETH: "https://coin-images.coingecko.com/coins/images/279/large/ethereum.png?1696501628",
  USDC: "https://coin-images.coingecko.com/coins/images/6319/large/USDC.png?1769615602",
  USD1: "https://coin-images.coingecko.com/coins/images/54977/large/USD1_1000x1000_transparent.png?1749297002",
  WLD: "https://coin-images.coingecko.com/coins/images/31069/large/worldcoin.jpeg?1696529903",
  HYPE: "https://coin-images.coingecko.com/coins/images/50882/large/hyperliquid.jpg?1729431300",
  ZEC: "https://coin-images.coingecko.com/coins/images/486/large/circle-zcash-color.png?1696501740",
  SOL: "https://coin-images.coingecko.com/coins/images/4128/large/solana.png?1718769756",
  BNB: "https://coin-images.coingecko.com/coins/images/825/large/bnb-icon2_2x.png?1696501970",
  XRP: "https://coin-images.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png?1696501442",
  XAUT: "https://coin-images.coingecko.com/coins/images/10481/large/logo.png?1774627372",
  BABY: "https://coin-images.coingecko.com/coins/images/55092/large/Baby-Symbol-Mint_%281%29.png?1744788866",
  NEAR: "https://coin-images.coingecko.com/coins/images/10365/large/near.jpg?1696510367",
  UNI: "https://coin-images.coingecko.com/coins/images/12504/large/uniswap-logo.png?1720676669",
  SPX: "https://coin-images.coingecko.com/coins/images/31401/large/centeredcoin_%281%29.png?1737048493",
  TAO: "https://coin-images.coingecko.com/coins/images/28452/large/ARUsPeNQ_400x400.jpeg?1696527447",
  XLM: "https://coin-images.coingecko.com/coins/images/100/large/fmpFRHHQ_400x400.jpg?1735231350",
  DOGE: "https://coin-images.coingecko.com/coins/images/5/large/dogecoin.png?1696501409",
  ADA: "https://coin-images.coingecko.com/coins/images/975/large/cardano.png?1696502090",
  SUI: "https://coin-images.coingecko.com/coins/images/26375/large/sui-ocean-square.png?1727791290",
  TRX: "https://coin-images.coingecko.com/coins/images/1094/large/photo_2026-04-13_09-59-16.png?1776048311",
  LINK: "https://coin-images.coingecko.com/coins/images/877/large/Chainlink_Logo_500.png?1760023405",
  POL: "https://coin-images.coingecko.com/coins/images/32440/large/pol.png?1759114181",
  DOT: "https://coin-images.coingecko.com/coins/images/12171/large/polkadot.jpg?1766533446",
  LTC: "https://coin-images.coingecko.com/coins/images/2/large/litecoin.png?1696501400",
  BCH: "https://coin-images.coingecko.com/coins/images/780/large/bitcoin-cash-circle.png?1696501932",
  AAVE: "https://coin-images.coingecko.com/coins/images/12645/large/aave-token-round.png?1720472354",
  ATOM: "https://coin-images.coingecko.com/coins/images/1481/large/cosmos_hub.png?1696502525",
  FIL: "https://coin-images.coingecko.com/coins/images/12817/large/filecoin.png?1696512609",
  ETC: "https://coin-images.coingecko.com/coins/images/453/large/ethereum-classic-logo.png?1696501717"
};

const pairs = [
  {
    symbol: "BTC/USDT",
    key: "BTCUSDT",
    coin: "btc",
    price: 72923.87,
    change: 1.42,
    volume: 28.42,
    marketCap: 1.61,
    futuresVol: 68.31,
    oi: 36.21,
    funding: 0.01,
    basis: 0.03,
    spread: 0.00621,
    maxSpread: 0.0248,
    imbalance: 0.1628,
    bidDepth: 2580000,
    askDepth: 2360000,
    buyWall: 30,
    sellWall: 27,
    liquidity: 94,
    suspicious: 18,
    slippage: 0.012,
    resilience: 0.88,
    regime: "High",
    ofi: 0.072,
    volatility: 0.0182,
    impact: 0.013
  },
  {
    symbol: "ETH/USDT",
    key: "ETHUSDT",
    coin: "eth",
    price: 3893.21,
    change: 2.18,
    volume: 16.53,
    marketCap: 245.7,
    futuresVol: 38.77,
    oi: 19.84,
    funding: 0.012,
    basis: 0.04,
    spread: 0.00687,
    maxSpread: 0.0264,
    imbalance: -0.1618,
    bidDepth: 1990000,
    askDepth: 2190000,
    buyWall: 26,
    sellWall: 25,
    liquidity: 90,
    suspicious: 42,
    slippage: 0.016,
    resilience: 0.83,
    regime: "High",
    ofi: 0.041,
    volatility: 0.0217,
    impact: 0.015
  },
  {
    symbol: "SOL/USDT",
    key: "SOLUSDT",
    coin: "sol",
    price: 172.63,
    change: 2.96,
    volume: 8.74,
    marketCap: 81.6,
    futuresVol: 15.92,
    oi: 7.12,
    funding: 0.015,
    basis: 0.05,
    spread: 0.00942,
    maxSpread: 0.0311,
    imbalance: -0.00985,
    bidDepth: 881000,
    askDepth: 932000,
    buyWall: 0,
    sellWall: 0,
    liquidity: 81,
    suspicious: 12,
    slippage: 0.021,
    resilience: 0.79,
    regime: "Medium",
    ofi: -0.032,
    volatility: 0.0308,
    impact: 0.02
  },
  {
    symbol: "XRP/USDT",
    key: "XRPUSDT",
    coin: "xrp",
    price: 0.5289,
    change: 1.74,
    volume: 3.21,
    marketCap: 29.8,
    futuresVol: 6.12,
    oi: 2.93,
    funding: 0.006,
    basis: 0.02,
    spread: 0.01031,
    maxSpread: 0.0384,
    imbalance: 0.08666,
    bidDepth: 631000,
    askDepth: 589000,
    buyWall: 0,
    sellWall: 0,
    liquidity: 64,
    suspicious: 15,
    slippage: 0.029,
    resilience: 0.7,
    regime: "Low",
    ofi: -0.061,
    volatility: 0.0337,
    impact: 0.026
  },
  {
    symbol: "BNB/USDT",
    key: "BNBUSDT",
    coin: "bnb",
    price: 612.18,
    change: 1.21,
    volume: 6.39,
    marketCap: 62.1,
    futuresVol: 12.15,
    oi: 4.71,
    funding: 0.008,
    basis: 0.03,
    spread: 0.00753,
    maxSpread: 0.0257,
    imbalance: 0.112,
    bidDepth: 742000,
    askDepth: 704000,
    buyWall: 18,
    sellWall: 11,
    liquidity: 78,
    suspicious: 22,
    slippage: 0.02,
    resilience: 0.76,
    regime: "Medium",
    ofi: -0.015,
    volatility: 0.0261,
    impact: 0.017
  },
  {
    symbol: "ADA/USDT",
    key: "ADAUSDT",
    coin: "ada",
    price: 0.4521,
    change: 1.68,
    volume: 2.34,
    marketCap: 16.8,
    futuresVol: 4.95,
    oi: 1.89,
    funding: 0.005,
    basis: 0.01,
    spread: 0.01246,
    maxSpread: 0.0422,
    imbalance: 0.028,
    bidDepth: 486000,
    askDepth: 462000,
    buyWall: 15,
    sellWall: 19,
    liquidity: 58,
    suspicious: 18,
    slippage: 0.034,
    resilience: 0.62,
    regime: "Medium",
    ofi: -0.026,
    volatility: 0.037,
    impact: 0.031
  },
  {
    symbol: "DOGE/USDT",
    key: "DOGEUSDT",
    coin: "doge",
    price: 0.1542,
    change: -0.81,
    volume: 1.87,
    marketCap: 13.9,
    futuresVol: 3.62,
    oi: 1.34,
    funding: -0.002,
    basis: -0.01,
    spread: 0.01492,
    maxSpread: 0.0488,
    imbalance: -0.088,
    bidDepth: 132000,
    askDepth: 126000,
    buyWall: 11,
    sellWall: 18,
    liquidity: 46,
    suspicious: 55,
    slippage: 0.041,
    resilience: 0.51,
    regime: "Fragile",
    ofi: -0.047,
    volatility: 0.041,
    impact: 0.038
  },
  {
    symbol: "AVAX/USDT",
    key: "AVAXUSDT",
    coin: "avax",
    price: 35.12,
    change: 2.31,
    volume: 1.42,
    marketCap: 14.2,
    futuresVol: 2.84,
    oi: 0.98,
    funding: 0.004,
    basis: 0.01,
    spread: 0.01125,
    maxSpread: 0.0441,
    imbalance: -0.032,
    bidDepth: 121000,
    askDepth: 113000,
    buyWall: 8,
    sellWall: 13,
    liquidity: 60,
    suspicious: 24,
    slippage: 0.039,
    resilience: 0.57,
    regime: "Medium",
    ofi: -0.036,
    volatility: 0.035,
    impact: 0.029
  }
];

const reports = [
  ["Daily Liquidity Summary", "Daily Summary", "May 20, 2025", "May 20, 2025 21:45", "Completed", "2.41 MB"],
  ["Weekly Market Overview", "Weekly Summary", "May 12 - May 18, 2025", "May 19, 2025 08:30", "Completed", "6.72 MB"],
  ["Monthly Performance Report", "Monthly Summary", "April 2025", "May 01, 2025 09:15", "Completed", "12.94 MB"],
  ["Market Making Performance", "Performance", "May 01 - May 20, 2025", "May 20, 2025 18:10", "Completed", "4.88 MB"],
  ["Inventory & Exposure Analysis", "Analysis", "May 01 - May 20, 2025", "May 20, 2025 17:05", "Completed", "3.16 MB"],
  ["Wall & Order Flow Report", "Special Report", "May 20, 2025", "May 20, 2025 20:20", "Completed", "2.93 MB"],
  ["Liquidity Provider Comparison", "Comparison", "April 2025", "Apr 30, 2025 11:40", "Completed", "7.51 MB"],
  ["Custom Strategy Review", "Custom Report", "May 01 - May 20, 2025", "May 20, 2025 16:30", "Processing", "-"]
];

let alerts = [
  ["22:14:57", "CRITICAL", "ETH/USDT", "Latency High", "1,256 ms", "Unacknowledged"],
  ["22:14:31", "CRITICAL", "BTC/USDT", "Spread Spike", "0.0248%", "Unacknowledged"],
  ["22:13:45", "WARNING", "SOL/USDT", "Liquidity Deterioration", "-38.6% (5m)", "Unacknowledged"],
  ["22:12:58", "WARNING", "XRP/USDT", "Suspicious Wall", "Bid Wall 2.8M USDT", "Acknowledged"],
  ["22:11:22", "INFO", "BNB/USDT", "Order Book Imbalance", "Buy 72% / Sell 28%", "Acknowledged"],
  ["22:10:05", "WARNING", "DOGE/USDT", "Spread Spike", "0.0182%", "Unacknowledged"],
  ["22:09:13", "INFO", "ADA/USDT", "Latency High", "842 ms", "Acknowledged"],
  ["22:08:44", "WARNING", "AVAX/USDT", "Liquidity Deterioration", "-25.4% (5m)", "Unacknowledged"]
];

function icon(name) {
  const paths = {
    grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    trend: '<path d="M3 17l6-6 4 4 7-9"/><path d="M14 6h6v6"/>',
    droplet: '<path d="M12 2s7 7.2 7 12a7 7 0 0 1-14 0c0-4.8 7-12 7-12z"/>',
    layers: '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 12l9 5 9-5"/><path d="M3 16l9 5 9-5"/>',
    bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    chart: '<path d="M4 19V5"/><path d="M4 19h16"/><rect x="7" y="11" width="3" height="5"/><rect x="12" y="7" width="3" height="9"/><rect x="17" y="3" width="3" height="13"/>',
    file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h6"/>',
    settings: '<path d="M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5z"/><path d="M19.4 15a1.8 1.8 0 0 0 .36 2l.05.05a2 2 0 1 1-2.83 2.83l-.05-.05a1.8 1.8 0 0 0-2-.36 1.8 1.8 0 0 0-1 1.64V21a2 2 0 1 1-4 0v-.09a1.8 1.8 0 0 0-1-1.64 1.8 1.8 0 0 0-2 .36l-.05.05a2 2 0 1 1-2.83-2.83l.05-.05a1.8 1.8 0 0 0 .36-2 1.8 1.8 0 0 0-1.64-1H3a2 2 0 1 1 0-4h.09a1.8 1.8 0 0 0 1.64-1 1.8 1.8 0 0 0-.36-2l-.05-.05a2 2 0 1 1 2.83-2.83l.05.05a1.8 1.8 0 0 0 2 .36h.02a1.8 1.8 0 0 0 1-1.64V3a2 2 0 1 1 4 0v.09a1.8 1.8 0 0 0 1 1.64h.02a1.8 1.8 0 0 0 2-.36l.05-.05a2 2 0 1 1 2.83 2.83l-.05.05a1.8 1.8 0 0 0-.36 2v.02a1.8 1.8 0 0 0 1.64 1H21a2 2 0 1 1 0 4h-.09a1.8 1.8 0 0 0-1.51 1z"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="M4.93 4.93l1.41 1.41"/><path d="M17.66 17.66l1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="M6.34 17.66l-1.41 1.41"/><path d="M19.07 4.93l-1.41 1.41"/>',
    download: '<path d="M12 3v12"/><path d="M7 10l5 5 5-5"/><path d="M4 21h16"/>',
    eye: '<path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    check: '<path d="M20 6L9 17l-5-5"/>',
    more: '<circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21"/>',
    refresh: '<path d="M21 12a9 9 0 0 1-15.5 6.2"/><path d="M3 12A9 9 0 0 1 18.5 5.8"/><path d="M3 19v-5h5"/><path d="M21 5v5h-5"/>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    plus: '<path d="M12 5v14"/><path d="M5 12h14"/>'
  };
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">${paths[name] || paths.grid}</svg>`;
}

function formatNumber(value, digits = 2) {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  }).format(value);
}

function compact(value) {
  if (value >= 1_000_000_000_000) return `${formatNumber(value / 1_000_000_000_000, 2)}T`;
  if (value >= 1_000_000_000) return `${formatNumber(value / 1_000_000_000, 2)}B`;
  if (value >= 1_000_000) return `${formatNumber(value / 1_000_000, 2)}M`;
  if (value >= 1_000) return `${formatNumber(value / 1_000, 1)}K`;
  return formatNumber(value, 0);
}

function money(value, suffix = "") {
  if (value >= 1000) return `$${compact(value)}${suffix}`;
  if (value >= 1) return `$${formatNumber(value, 2)}${suffix}`;
  return `$${formatNumber(value, 4)}${suffix}`;
}

function signedPercent(value, digits = 2) {
  const numeric = asNumber(value);
  return `${numeric >= 0 ? "+" : ""}${numeric.toFixed(digits)}%`;
}

function asNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function average(items, key) {
  return items.reduce((sum, item) => sum + item[key], 0) / items.length;
}

function nowLabel() {
  return state.lastUpdate.toLocaleString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  });
}

function values(seed, length = 28, volatility = 0.4, trend = 0.02) {
  let x = seed * 8.13 + 4;
  return Array.from({ length }, (_, index) => {
    x += Math.sin(index * 0.8 + seed) * volatility + trend * index + (Math.random() - 0.5) * volatility;
    return Math.max(0.1, x);
  });
}

function pathFromValues(series, width = 120, height = 32, pad = 2) {
  const min = Math.min(...series);
  const max = Math.max(...series);
  const range = max - min || 1;
  const denominator = Math.max(1, series.length - 1);
  return series
    .map((value, index) => {
      const x = pad + (index / denominator) * (width - pad * 2);
      const y = height - pad - ((value - min) / range) * (height - pad * 2);
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}

function sparkline(series, color = palette.blue, fill = false) {
  const line = pathFromValues(series, 120, 34, 3);
  const fillPath = `${line} L117 34 L3 34 Z`;
  return `
    <svg class="spark" viewBox="0 0 120 34" preserveAspectRatio="none">
      ${fill ? `<path d="${fillPath}" fill="${color}" opacity="0.16"></path>` : ""}
      <path d="${line}" fill="none" stroke="${color}" stroke-width="2" vector-effect="non-scaling-stroke"></path>
    </svg>
  `;
}

function lineChart(seriesList, options = {}) {
  const width = 480;
  const height = options.height || 210;
  const pad = { left: 42, top: 18, right: 18, bottom: 34 };
  const all = seriesList.flatMap((s) => s.values);
  const min = options.min ?? Math.min(...all);
  const max = options.max ?? Math.max(...all);
  const range = max - min || 1;
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const grid = [0, 0.25, 0.5, 0.75, 1]
    .map((t) => {
      const y = pad.top + innerH * t;
      return `<path d="M${pad.left} ${y}H${width - pad.right}" stroke="rgba(150,186,219,.13)" stroke-dasharray="3 4"></path>`;
    })
    .join("");
  const lines = seriesList
    .map((series) => {
      const pointDenominator = Math.max(1, series.values.length - 1);
      const d = series.values
        .map((value, index) => {
          const x = pad.left + (index / pointDenominator) * innerW;
          const y = pad.top + innerH - ((value - min) / range) * innerH;
          return `${index === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
        })
        .join(" ");
      const fillPath = `${d} L${width - pad.right} ${height - pad.bottom} L${pad.left} ${height - pad.bottom} Z`;
      return `
        ${series.fill ? `<path d="${fillPath}" fill="${series.color}" opacity="${series.opacity || 0.14}"></path>` : ""}
        <path d="${d}" fill="none" stroke="${series.color}" stroke-width="${series.width || 2.2}" vector-effect="non-scaling-stroke"></path>
      `;
    })
    .join("");
  const labels = (options.labels || ["21:15", "21:30", "21:45", "22:00", "22:15"])
    .map((label, index, arr) => {
      const labelDenominator = Math.max(1, arr.length - 1);
      const x = pad.left + (index / labelDenominator) * innerW;
      return `<text x="${x}" y="${height - 10}" text-anchor="middle" fill="#9db2c9" font-size="11">${label}</text>`;
    })
    .join("");
  return `
    <div class="chart ${options.compact ? "compact" : ""}">
      <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
        ${grid}
        <path d="M${pad.left} ${pad.top}V${height - pad.bottom}H${width - pad.right}" fill="none" stroke="rgba(150,186,219,.22)"></path>
        ${lines}
        ${labels}
        ${options.badge ? `<rect x="${width - 95}" y="${height / 2 - 12}" width="72" height="24" rx="4" fill="rgba(45,140,255,.72)"></rect><text x="${width - 59}" y="${height / 2 + 4}" text-anchor="middle" fill="#fff" font-size="12">${options.badge}</text>` : ""}
      </svg>
    </div>
  `;
}

function scoreRing(score) {
  const color = score >= 75 ? palette.green : score >= 50 ? palette.amber : palette.red;
  return `<span class="score-ring" style="--ring:${score}%;--ring-color:${color}">${score}</span>`;
}

function pairDigits(pair) {
  return asNumber(pair?.price) < 1 ? 8 : 4;
}

function pairBestBid(pair) {
  return asNumber(pair?.bestBid, asNumber(pair?.bids?.[0]?.[0], asNumber(pair?.price) * 0.999998));
}

function pairBestAsk(pair) {
  return asNumber(pair?.bestAsk, asNumber(pair?.asks?.[0]?.[0], asNumber(pair?.price) * 1.000002));
}

function pairBidQty(pair) {
  return asNumber(pair?.bidQty, asNumber(pair?.bids?.[0]?.[1]));
}

function pairAskQty(pair) {
  return asNumber(pair?.askQty, asNumber(pair?.asks?.[0]?.[1]));
}

function pairMarketCapUsd(pair) {
  return asNumber(pair?.marketCap) * 1_000_000_000;
}

function pairVolumeUsd(pair) {
  return asNumber(pair?.volume24h, asNumber(pair?.volume) * 1_000_000_000);
}

function pairFuturesVolumeUsd(pair) {
  return asNumber(pair?.futuresVol) * 1_000_000_000;
}

function pairOpenInterestUsd(pair) {
  return asNumber(pair?.oi) * 1_000_000_000;
}

function nextFundingLabel(now = state.lastUpdate) {
  const date = now instanceof Date ? now : new Date(now);
  const next = new Date(date);
  const nextHour = Math.ceil((date.getUTCHours() + 1) / 8) * 8;
  next.setUTCMinutes(0, 0, 0);
  if (nextHour >= 24) {
    next.setUTCDate(next.getUTCDate() + 1);
    next.setUTCHours(0);
  } else {
    next.setUTCHours(nextHour);
  }
  return next.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false });
}

function metricCardsOverview() {
  const kpis = state.kpis || {};
  const ws = state.wallSummary || {};
  const tf = state.timeframe;

  // Spread from backend KPIs or fallback from pairs
  const avgSpread = kpis.averageSpread != null
    ? kpis.averageSpread.toFixed(6)
    : (pairs.length ? formatNumber(pairs.reduce((s, p) => s + (p.spread || 0), 0) / pairs.length, 6) : "—");
  const maxSpread = kpis.maxSpread != null
    ? kpis.maxSpread.toFixed(6)
    : (pairs.length ? formatNumber(Math.max(...pairs.map(p => p.spread || 0)), 6) : "—");

  // Imbalance: average absolute imbalance
  const avgImbalanceRaw = pairs.length
    ? pairs.reduce((s, p) => s + (p.imbalance || 0), 0) / pairs.length
    : 0;
  const avgImbalance = formatNumber(Math.abs(avgImbalanceRaw), 4);
  const imbalanceDir = avgImbalanceRaw >= 0 ? "good" : "bad";

  // Depth from backend KPIs or pair data
  const bidDepth = kpis.bidDepthTop10 != null
    ? compact(kpis.bidDepthTop10)
    : (pairs.length ? compact(pairs.reduce((s, p) => s + (p.bidDepth || 0), 0)) : "—");
  const askDepth = kpis.askDepthTop10 != null
    ? compact(kpis.askDepthTop10)
    : (pairs.length ? compact(pairs.reduce((s, p) => s + (p.askDepth || 0), 0)) : "—");

  // Wall counts from wall summary or pair fields
  const buyCount = ws.buyWallCount != null
    ? ws.buyWallCount
    : pairs.reduce((s, p) => s + (p.buyWall || 0), 0);
  const sellCount = ws.sellWallCount != null
    ? ws.sellWallCount
    : pairs.reduce((s, p) => s + (p.sellWall || 0), 0);
  const totalWalls = buyCount + sellCount;
  const wallBiasText = ws.wallBias || (buyCount >= sellCount ? "Buyer Pressure" : "Seller Pressure");
  const wallBiasVal = totalWalls > 0 ? Math.round((buyCount / totalWalls) * 100) : 50;
  const wallBiasDir = buyCount >= sellCount ? "good" : "bad";
  const wallBiasColor = wallBiasDir === "good" ? palette.green : palette.red;

  // Slippage
  const slippageRaw = kpis.slippageEstimate != null
    ? kpis.slippageEstimate
    : (pairs.length ? pairs.reduce((s, p) => s + (p.slippage || 0), 0) / pairs.length : 0.018);
  const slippageDisplay = slippageRaw.toFixed(4);
  const slippageGaugeVal = Math.min(100, slippageRaw * 2500);
  const slippageDir = slippageGaugeVal < 33 ? "good" : slippageGaugeVal < 66 ? "warn" : "bad";
  const slippageDeltaText = slippageGaugeVal < 33 ? "Low" : slippageGaugeVal < 66 ? "Medium" : "High";
  const slippageColor = slippageDir === "good" ? palette.green : slippageDir === "warn" ? palette.amber : palette.red;

  return [
    kpiCard({ title: `Avg Spread (${tf})`, value: avgSpread, unit: "%", delta: `${tf} snapshot`, direction: "good", color: palette.blue, series: values(1, 28, 0.35) }),
    kpiCard({ title: `Max Spread (${tf})`, value: maxSpread, unit: "%", delta: `${tf} snapshot`, direction: "bad", color: palette.blue, series: values(2, 28, 0.42, 0.01) }),
    kpiCard({ title: `Avg Imbalance (${tf})`, value: avgImbalance, delta: `${avgImbalanceRaw >= 0 ? "Buy" : "Sell"} bias`, direction: imbalanceDir, color: palette.green, series: values(3, 28, 0.35, -0.01) }),
    kpiCard({ title: "Bid Depth (Top 10)", value: bidDepth, unit: "USDT", delta: `${tf} snapshot`, direction: "good", color: palette.blue, series: values(4, 28, 0.32) }),
    kpiCard({ title: "Ask Depth (Top 10)", value: askDepth, unit: "USDT", delta: `${tf} snapshot`, direction: "bad", color: palette.blue, series: values(5, 28, 0.34) }),
    kpiCard({ title: `Buy Walls (${tf})`, value: String(buyCount), delta: "detected in interval", direction: "good", color: palette.green, series: values(6, 28, 0.42) }),
    kpiCard({ title: `Sell Walls (${tf})`, value: String(sellCount), delta: "detected in interval", direction: "bad", color: palette.red, series: values(7, 28, 0.4) }),
    kpiCard({
      title: "Wall Bias",
      value: wallBiasText,
      delta: `${buyCount} Buy / ${sellCount} Sell`,
      direction: wallBiasDir,
      color: wallBiasColor,
      extra: miniGauge(wallBiasVal, wallBiasColor, ["Sell", "Neutral", "Buy"])
    }),
    kpiCard({
      title: `Slippage Est. (${tf})`,
      value: slippageDisplay,
      unit: "%",
      delta: slippageDeltaText,
      direction: slippageDir,
      color: slippageColor,
      extra: miniGauge(slippageGaugeVal, slippageColor, ["Low", "Med", "High"])
    }),
    kpiCard({ title: "Pair Count", value: String(pairs.length), delta: "Active pairs", direction: "good", color: palette.cyan, series: values(8, 28, 0.2) })
  ].join("");
}

function miniGauge(value, color, labels = []) {
  const clamped = Math.max(0, Math.min(100, value));
  const cx = 80;
  const cy = 70;
  const needleLength = 42;
  const angle = (180 + clamped * 1.8) * (Math.PI / 180);
  const needleX = cx + Math.cos(angle) * needleLength;
  const needleY = cy + Math.sin(angle) * needleLength;
  const ticks = [0, 25, 50, 75, 100]
    .map((tick) => {
      const tickAngle = (180 + tick * 1.8) * (Math.PI / 180);
      const x1 = cx + Math.cos(tickAngle) * 49;
      const y1 = cy + Math.sin(tickAngle) * 49;
      const x2 = cx + Math.cos(tickAngle) * 56;
      const y2 = cy + Math.sin(tickAngle) * 56;
      return `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="rgba(217,232,247,.36)" stroke-width="2" stroke-linecap="round"></line>`;
    })
    .join("");
  return `
    <div class="dial-gauge" style="--dial-color:${color};--dial-value:${clamped}">
      <svg viewBox="0 0 160 86" role="img" aria-label="Gauge ${clamped}">
        <path class="dial-track" d="M24 70A56 56 0 0 1 136 70" pathLength="100"></path>
        <path class="dial-active" d="M24 70A56 56 0 0 1 136 70" pathLength="100" stroke-dasharray="${clamped} 100"></path>
        <g class="dial-ticks">${ticks}</g>
        <line class="dial-needle" x1="${cx}" y1="${cy}" x2="${needleX.toFixed(1)}" y2="${needleY.toFixed(1)}"></line>
        <circle class="dial-pivot" cx="${cx}" cy="${cy}" r="5"></circle>
        ${
          labels.length
            ? `<text x="26" y="84" class="dial-label" text-anchor="start">${labels[0]}</text><text x="80" y="31" class="dial-label" text-anchor="middle">${labels[1]}</text><text x="134" y="84" class="dial-label" text-anchor="end">${labels[2]}</text>`
            : ""
        }
      </svg>
    </div>
  `;
}

function marketOverviewTable() {
  const total = pairs.length;
  const pageSize = state.overviewPageSize;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  state.overviewPage = Math.min(Math.max(1, state.overviewPage), pageCount);
  const start = (state.overviewPage - 1) * pageSize;
  const end = Math.min(start + pageSize, total);
  const pagePairs = pairs.slice(start, end);
  const rows = pagePairs.map((pair, pageIndex) => {
    const index = start + pageIndex;
    const condition = pair.imbalance > 0.08 ? "BUYER DOMINANT" : pair.imbalance < -0.08 ? "SELLER DOMINANT" : "NEUTRAL";
    const status = pair.liquidity > 75 ? "Healthy" : pair.liquidity > 55 ? "Caution" : "Low";
    const digits = pairDigits(pair);
    const bestBid = pairBestBid(pair);
    const bestAsk = pairBestAsk(pair);
    const bidQty = pairBidQty(pair);
    const askQty = pairAskQty(pair);
    const rowTime = new Date(state.lastUpdate.getTime() - index * 7000).toLocaleString("en-GB", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false
    });
    return `
      <tr>
        <td>${rowTime.replace(", ", "<br>")}</td>
        <td>${pairMarkup(pair)}</td>
        <td class="text-good">${formatNumber(bestBid, digits)}</td>
        <td class="text-bad">${formatNumber(bestAsk, digits)}</td>
        <td><span class="text-info">|||</span> ${pair.spread.toFixed(6)}</td>
        <td class="text-good">${formatNumber(bidQty, 4)}</td>
        <td class="text-bad">${formatNumber(askQty, 4)}</td>
        <td class="${pair.imbalance >= 0 ? "text-good" : "text-bad"}">${pair.imbalance.toFixed(4)}</td>
        <td>${statusBadge(condition)}</td>
        <td class="text-good">${pair.buyWall}</td>
        <td class="text-bad">${pair.sellWall}</td>
        <td>${statusBadge(status)}</td>
        <td>${scoreRing(pair.suspicious)}</td>
      </tr>
    `;
  });
  const pageButtons = Array.from({ length: pageCount }, (_, index) => {
    const page = index + 1;
    return `<button class="segment ${state.overviewPage === page ? "is-active" : ""}" data-action="overview-page" data-page="${page}">${page}</button>`;
  }).join("");
  return `
    <div>
      <div class="table-shell">
        <table>
          <thead>
            <tr>
              <th>Time</th><th>Symbol</th><th>Best Bid<br>(USDT)</th><th>Best Ask<br>(USDT)</th><th>Spread %</th>
              <th>Bid Qty<br>(Base)</th><th>Ask Qty<br>(Base)</th><th>Imbalance</th><th>Condition</th>
              <th>Buy Wall</th><th>Sell Wall</th><th>Liquidity Status</th><th>Suspicious<br>Score</th>
            </tr>
          </thead>
          <tbody>${rows.join("")}</tbody>
        </table>
      </div>
      <div class="status-footer overview-pagination">
        <span>Showing ${total ? start + 1 : 0} to ${end} of ${total} pairs</span>
        <div class="status-row">
          <button class="table-button" data-action="overview-page" data-page="${state.overviewPage - 1}" ${state.overviewPage === 1 ? "disabled" : ""}>&lt;</button>
          ${pageButtons}
          <button class="table-button" data-action="overview-page" data-page="${state.overviewPage + 1}" ${state.overviewPage === pageCount ? "disabled" : ""}>&gt;</button>
        </div>
      </div>
    </div>
  `;
}

function generateTimeLabels(interval, count = 5) {
  const now = state.lastUpdate instanceof Date ? state.lastUpdate : new Date();
  const stepMs = {
    "1s": 1000, "5s": 5000, "15s": 15000, "30s": 30000,
    "1m": 60000, "5m": 300000, "15m": 900000, "30m": 1800000,
    "1h": 3600000, "4h": 14400000, "12h": 43200000,
    "1D": 86400000, "1W": 604800000, "1M": 2592000000
  }[interval] || 300000;
  const labels = [];
  for (let i = count - 1; i >= 0; i--) {
    const t = new Date(now.getTime() - i * stepMs);
    let label;
    if (stepMs < 60000) {
      label = t.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
    } else if (stepMs < 86400000) {
      label = t.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false });
    } else {
      label = t.toLocaleDateString("en-GB", { day: "2-digit", month: "2-digit" });
    }
    labels.push(label);
  }
  return labels;
}

function orderBookSnapshot(pair = pairs[0]) {
  // Use real bids/asks from backend when available
  const rawBids = Array.isArray(pair.bids) && pair.bids.length > 0 ? pair.bids : null;
  const rawAsks = Array.isArray(pair.asks) && pair.asks.length > 0 ? pair.asks : null;

  // Build depth chart data
  const bidValues = rawBids
    ? rawBids.slice(0, 18).map(([, qty]) => Math.max(0.01, parseFloat(qty))).reverse()
    : values(10, 18, 0.3, -0.03).map((v, i) => Math.max(0.2, v + (18 - i) * 0.12));
  const askValues = rawAsks
    ? rawAsks.slice(0, 18).map(([, qty]) => Math.max(0.01, parseFloat(qty)))
    : values(11, 18, 0.24, 0.04).map((v, i) => Math.max(0.2, v + i * 0.14));

  const depthSvg = (series, color, flip = false) => {
    const d = pathFromValues(series, 240, 180, 0);
    const path = `${d} ${flip ? "L0 180" : "L240 180"} Z`;
    return `<svg viewBox="0 0 240 180" preserveAspectRatio="none"><path d="${path}" fill="${color}" opacity=".32"></path><path d="${d}" stroke="${color}" fill="none" stroke-width="2.2"></path></svg>`;
  };

  // Order book rows: use real data if available
  const topBids = rawBids ? rawBids.slice(0, 5) : null;
  const topAsks = rawAsks ? rawAsks.slice(0, 5) : null;
  const digits = pair.price < 1 ? 4 : 2;

  const bidRows = Array.from({ length: 5 }, (_, i) => {
    if (topBids && topBids[i]) {
      const [price, qty] = topBids[i];
      const p = parseFloat(price), q = parseFloat(qty);
      return `<tr><td>${compact(p * q)}</td><td class="text-good">${formatNumber(p, digits)}</td></tr>`;
    }
    return `<tr><td>${compact(pair.bidDepth * (1 - i * 0.14))}</td><td class="text-good">${formatNumber(pair.price - (i + 1) * pair.price * 0.0001, digits)}</td></tr>`;
  });

  const askRows = Array.from({ length: 5 }, (_, i) => {
    if (topAsks && topAsks[i]) {
      const [price, qty] = topAsks[i];
      const p = parseFloat(price), q = parseFloat(qty);
      return `<tr><td class="text-bad">${formatNumber(p, digits)}</td><td>${compact(p * q)}</td></tr>`;
    }
    return `<tr><td class="text-bad">${formatNumber(pair.price + (i + 1) * pair.price * 0.0001, digits)}</td><td>${compact(pair.askDepth * (1 - i * 0.13))}</td></tr>`;
  });

  // Best bid/ask for display
  const bestBid = rawBids ? parseFloat(rawBids[0][0]) : pair.price * 0.999998;
  const bestAsk = rawAsks ? parseFloat(rawAsks[0][0]) : pair.price * 1.000002;
  const spreadPct = pair.spread != null ? pair.spread : 0;

  return `
    <div class="orderbook">
      <div>
        <div class="text-good" style="font-weight:750;margin-bottom:6px">Bid Depth</div>
        <div class="depth-side">${depthSvg(bidValues, palette.green, true)}</div>
      </div>
      <div class="mid-price">
        <div>
          <span>Spread ${spreadPct.toFixed(6)}%</span>
          <strong>${formatNumber(pair.price, digits)}</strong>
          <span class="text-good">${formatNumber(bestBid, digits)}</span>
          <span style="color:var(--muted);margin:0 4px">/</span>
          <span class="text-bad">${formatNumber(bestAsk, digits)}</span>
        </div>
      </div>
      <div>
        <div class="text-bad" style="font-weight:750;text-align:right;margin-bottom:6px">Ask Depth</div>
        <div class="depth-side">${depthSvg(askValues, palette.red)}</div>
      </div>
    </div>
    <div class="book-table">
      <div class="table-shell">
        <table><thead><tr><th>Bid Size (USDT)</th><th>Bid Price</th></tr></thead><tbody>${bidRows.join("")}</tbody></table>
      </div>
      <div class="table-shell">
        <table><thead><tr><th>Ask Price</th><th>Ask Size (USDT)</th></tr></thead><tbody>${askRows.join("")}</tbody></table>
      </div>
    </div>
    <div class="status-footer" style="margin-top:8px">
      <span style="font-size:11px;color:var(--muted)">${rawBids ? `Live order book — ${rawBids.length} bid levels, ${(rawAsks||[]).length} ask levels` : "Estimated from depth snapshot"}</span>
    </div>
  `;
}

function renderOverview() {
  const selected = pairs.find((pair) => pair.symbol === state.selectedPair) || pairs[0];
  const tf = state.timeframe;
  const kpis = state.kpis || {};
  const chartPairs = pairs.slice(0, 8);
  const chartLabels = chartPairs.length ? chartPairs.map((pair) => tokenFromPair(pair)) : ["-"];

  // Derived KPI values for chart badges
  const avgSpreadBadge = kpis.averageSpread != null
    ? `${kpis.averageSpread.toFixed(6)}%`
    : (pairs.length ? `${formatNumber(pairs.reduce((s, p) => s + (p.spread || 0), 0) / pairs.length, 6)}%` : "—");
  const avgImbalanceBadge = pairs.length
    ? formatNumber(Math.abs(pairs.reduce((s, p) => s + (p.imbalance || 0), 0) / pairs.length), 4)
    : "—";

  const spreadSeries = chartPairs.length ? chartPairs.map((pair) => asNumber(pair.spread)) : [0];
  const imbalanceBars = chartPairs.map((pair) => ({
    label: tokenFromPair(pair),
    value: Number((asNumber(pair.imbalance) * 100).toFixed(2)),
    color: asNumber(pair.imbalance) >= 0 ? palette.green : palette.red
  }));
  const wallBiasBars = chartPairs.map((pair) => {
    const netWalls = asNumber(pair.buyWall) - asNumber(pair.sellWall);
    return {
      label: tokenFromPair(pair),
      value: netWalls,
      color: netWalls >= 0 ? palette.green : palette.red
    };
  });
  const bidDepthSeries = chartPairs.length ? chartPairs.map((pair) => asNumber(pair.bidDepth)) : [0];
  const askDepthSeries = chartPairs.length ? chartPairs.map((pair) => asNumber(pair.askDepth)) : [0];

  return `
    <div class="grid kpi-grid ten">${metricCardsOverview()}</div>
    <div class="grid layout-overview">
      ${panel(`Market Overview (${tf})`, marketOverviewTable())}
      ${panel(
        "Liquidity Analytics",
        `
          <div class="mini-chart-grid">
            ${miniChart(`Spread Snapshot (${tf})`, lineChart([{ values: spreadSeries, color: palette.blue }], { compact: true, badge: avgSpreadBadge, labels: chartLabels }), `<select class="mini-select"><option>Avg Spread</option></select>`)}
            ${miniChart(`Imbalance by Pair (${tf})`, barChart(imbalanceBars, { compact: true, hasNegative: true }), `<select class="mini-select"><option>${avgImbalanceBadge}</option></select>`)}
            ${miniChart(`Net Wall Bias (${tf})`, barChart(wallBiasBars, { compact: true, hasNegative: true, showValues: true }))}
            ${miniChart(`Order Book Depth (${tf})`, lineChart([{ values: bidDepthSeries, color: palette.green, fill: true }, { values: askDepthSeries, color: palette.red, fill: true }], { compact: true, labels: chartLabels }))}
          </div>
        `,
        ""
      )}
    </div>
    <div class="grid dual-panels">
      ${panel(
        `${icon("chart")} Market Maker Insights`,
        renderInsights()
      )}
      ${panel(`Order Book Snapshot (${selected.key}) — ${tf}`, orderBookSnapshot(selected))}
    </div>
  `;
}

function miniChart(title, body, actions = "") {
  return `<div class="mini-chart"><div class="panel-header"><h3>${title}</h3><div class="panel-actions">${actions}</div></div>${body}</div>`;
}

function insight(iconName, label, title, text, tone) {
  const color = tone === "warn" ? palette.amber : tone === "bad" ? palette.red : palette.green;
  return `
    <article class="insight-card">
      <div class="icon-bubble" style="color:${color};background:${color}20">${icon(iconName)}</div>
      <h3>${label}</h3>
      <strong class="${tone === "warn" ? "text-warn" : tone === "bad" ? "text-bad" : "text-good"}">${title}</strong>
      <p>${text}</p>
    </article>
  `;
}

function renderInsights() {
  const ins = state.insights;
  const ws = state.wallSummary || {};
  const kpis = state.kpis || {};
  const iconMap = { "Overall Market": "shield", "Buyer vs Seller": "trend", "Risk / Attention": "bell", "Slippage Outlook": "droplet" };

  // Use backend insights if available
  let insightCards;
  if (ins && ins.length > 0) {
    insightCards = ins.slice(0, 4).map((item) => {
      const iconName = iconMap[item.label] || "shield";
      return insight(iconName, item.label, item.title, item.text, item.tone || "good");
    });
  } else {
    // Derive from real state data
    const buyCount = ws.buyWallCount ?? pairs.reduce((s, p) => s + (p.buyWall || 0), 0);
    const sellCount = ws.sellWallCount ?? pairs.reduce((s, p) => s + (p.sellWall || 0), 0);
    const biasText = ws.wallBias || (buyCount >= sellCount ? "Buyer Pressure" : "Seller Pressure");
    const biasTone = buyCount >= sellCount ? "good" : "warn";
    const liqScore = kpis.liquidityScore ?? (pairs.length ? pairs.reduce((s, p) => s + (p.liquidity || 0), 0) / pairs.length : 70);
    const liqText = liqScore >= 70 ? "Healthy Liquidity" : liqScore >= 50 ? "Liquidity Needs Attention" : "Low Liquidity";
    const liqTone = liqScore >= 70 ? "good" : liqScore >= 50 ? "warn" : "bad";
    const slipRaw = kpis.slippageEstimate ?? (pairs.length ? pairs.reduce((s, p) => s + (p.slippage || 0), 0) / pairs.length : 0.02);
    const slipText = slipRaw < 0.03 ? "Low Slippage" : "Elevated Slippage";
    const slipTone = slipRaw < 0.03 ? "good" : "warn";
    const riskPair = pairs.length ? pairs.reduce((a, b) => (a.liquidity || 0) < (b.liquidity || 0) ? a : b) : null;
    const riskText = riskPair ? `${riskPair.symbol} has the weakest liquidity score in the selected group.` : "All pairs within normal range.";
    const riskTone = riskPair && (riskPair.liquidity || 0) < 60 ? "warn" : "good";
    insightCards = [
      insight("shield", "Overall Market", liqText, liqScore >= 70 ? `Avg liquidity ${liqScore.toFixed(1)}/100 — spreads tight and stable across ${pairs.length} pairs.` : "Liquidity conditions are uneven and should be monitored closely.", liqTone),
      insight("trend", "Buyer vs Seller", biasText, `Buy walls: ${buyCount}, Sell walls: ${sellCount} detected this ${state.timeframe}.`, biasTone),
      insight("bell", "Risk / Attention", riskPair && (riskPair.liquidity || 0) < 60 ? "Caution" : "Stable", riskText, riskTone),
      insight("droplet", "Slippage Outlook", slipText, slipRaw < 0.03 ? `Est. slippage ${(slipRaw * 100).toFixed(4)}% — low across major pairs under current conditions.` : `Est. slippage ${(slipRaw * 100).toFixed(4)}% — increasing, may affect larger orders.`, slipTone)
    ];
  }

  // Footer: dynamic based on insights
  const criticalCount = (ins && ins.length > 0 ? ins : []).filter((i) => i.tone === "bad").length;
  const cautionCount = (ins && ins.length > 0 ? ins : []).filter((i) => i.tone === "warn").length;
  return `
    <div class="grid overview-insights">
      ${insightCards.join("")}
    </div>
    <div class="status-footer">
      <div class="status-row">
        <span><span class="status-dot" style="background:${criticalCount > 0 ? palette.red : palette.green}"></span>${criticalCount > 0 ? `${criticalCount} critical issue(s)` : "No critical alerts"}</span>
        <span><span class="status-dot" style="background:${cautionCount > 0 ? palette.amber : palette.green}"></span>${cautionCount > 0 ? `${cautionCount} pair(s) need attention` : "All markets stable"}</span>
        <span><span class="status-dot"></span>All systems operational</span>
        <span><span class="status-dot"></span>Source: ${state.exchange} — ${state.timeframe}</span>
      </div>
    </div>
  `;
}

function renderMarkets() {
  const summary = state.marketSummary || {};
  const totalMarketCap = summary.totalMarketCap ?? pairs.reduce((sum, pair) => sum + pairMarketCapUsd(pair), 0);
  const spotVolume = summary.spotVolume24h ?? pairs.reduce((sum, pair) => sum + pairVolumeUsd(pair), 0);
  const futuresVolume = summary.futuresVolume24h ?? pairs.reduce((sum, pair) => sum + pairFuturesVolumeUsd(pair), 0);
  const btcDominance = summary.btcDominance ?? ((pairMarketCapUsd(pairs.find((pair) => pair.key === "BTCUSDT")) / Math.max(totalMarketCap, 1)) * 100);
  const ethDominance = summary.ethDominance ?? ((pairMarketCapUsd(pairs.find((pair) => pair.key === "ETHUSDT")) / Math.max(totalMarketCap, 1)) * 100);
  const fearGreed = Math.round(summary.fearGreedIndex ?? 50);
  const avgChange = pairs.length ? pairs.reduce((sum, pair) => sum + asNumber(pair.change), 0) / pairs.length : 0;
  const marketRows = pairs.map((pair, index) => {
    const marketCap = pairMarketCapUsd(pair);
    const volume = pairVolumeUsd(pair);
    const volumeToCap = marketCap > 0 ? (volume / marketCap) * 100 : 0;
    const bid = pairBestBid(pair);
    const ask = pairBestAsk(pair);
    const digits = pairDigits(pair);
    return `
    <tr>
      <td>${index + 1}</td><td>${pairMarkup(pair)}</td><td>${money(pair.price)}</td>
      <td class="${pair.change >= 0 ? "text-good" : "text-bad"}">${signedPercent(pair.change)}</td>
      <td>${money(volume)}</td><td>${money(marketCap)}</td>
      <td>${formatNumber(volumeToCap, 2)}%</td><td>${money(pairFuturesVolumeUsd(pair))}</td><td>${money(pairOpenInterestUsd(pair))}</td>
      <td class="${pair.funding >= 0 ? "text-good" : "text-bad"}">${pair.funding.toFixed(4)}%</td><td>${nextFundingLabel()}</td>
      <td class="${pair.basis >= 0 ? "text-good" : "text-bad"}">${signedPercent(pair.basis, 2)}</td>
      <td><span class="text-good">${formatNumber(bid, digits)}</span> / <span class="text-bad">${formatNumber(ask, digits)}</span></td>
    </tr>
  `;
  });
  return `
    <div class="grid kpi-grid">
      ${kpiCard({ title: "Total Market Cap", value: money(totalMarketCap), delta: `${pairs.length} active pairs`, direction: avgChange >= 0 ? "good" : "bad", color: palette.blue, series: marketCapSeries() })}
      ${kpiCard({ title: "24H Spot Volume", value: money(spotVolume), delta: `${state.exchange} spot`, color: palette.blue, series: volumeSeries("spot") })}
      ${kpiCard({ title: "24H Futures Volume", value: money(futuresVolume), delta: `${state.exchange} futures`, color: palette.blue, series: volumeSeries("futures") })}
      ${kpiCard({ title: "BTC Dominance", value: formatNumber(btcDominance, 2), unit: "%", delta: "market share", direction: "good", color: palette.orange, series: values(23, 28, 0.25) })}
      ${kpiCard({ title: "ETH Dominance", value: formatNumber(ethDominance, 2), unit: "%", delta: "market share", direction: "good", color: palette.violet, series: values(24, 28, 0.27) })}
      ${panel("Fear & Greed Index", `<div style="display:grid;grid-template-columns:130px 1fr;gap:14px;align-items:center">${gauge(fearGreed, fearGreed >= 75 ? "Extreme Greed" : fearGreed >= 55 ? "Greed" : fearGreed >= 45 ? "Neutral" : "Fear")}<div><strong>${state.exchange} market tone</strong><div class="bar-track" style="margin-top:14px"><div class="bar-fill" style="--bar:${fearGreed}%;background:linear-gradient(90deg,var(--red),var(--amber),var(--green))"></div></div></div></div>`)}
    </div>
    <div class="grid markets-layout">
      <div class="market-main grid triple-panels">
        ${panel("Market Heatmap", heatmap(), `<div class="tabs"><button class="tab is-active">Market Cap</button><button class="tab">24H Change</button></div>`)}
        ${panel("Top Movers (24H)", topMovers(), tabButtons("topMover", [["gainers", "Gainers"], ["losers", "Losers"], ["volume", "High Volume"]], state.topMoverTab))}
        ${panel("Futures vs Spot Performance", futuresSpot(), tabButtons("futures", [["24H", "24H"], ["7D", "7D"], ["30D", "30D"]], state.futuresTab))}
      </div>
      <div class="market-side">
        ${panel("Market Analytics", marketAnalytics())}
      </div>
    </div>
    <div class="grid dual-panels">
      ${panel(`Price Snapshot (${state.timeframe})`, priceTrendCards())}
      ${panel("Funding Bias Summary (8H)", fundingDonut())}
    </div>
    ${panel("Market Overview", `<div class="table-shell"><table><thead><tr><th>#</th><th>Symbol</th><th>Price</th><th>24H %</th><th>24H Volume</th><th>Market Cap</th><th>Spot Vol / MCap</th><th>Futures Vol</th><th>OI</th><th>Funding</th><th>Next Funding</th><th>Basis</th><th>Bid / Ask</th></tr></thead><tbody>${marketRows.join("")}</tbody></table></div>`)}
    ${footerStatus(`Data source: ${state.exchange}`, `Source status: ${state.sourceStatus}`, `${pairs.length} active pairs`, `Last update: ${nowLabel()} (UTC+7)`)}
  `;
}

function heatmap() {
  const maxCap = Math.max(...pairs.map(pairMarketCapUsd), 1);
  const data = pairs.slice(0, 10).map((pair, index) => [
    tokenFromPair(pair),
    signedPercent(pair.change),
    money(pairMarketCapUsd(pair)),
    Math.max(0.22, Math.min(0.9, pairMarketCapUsd(pair) / maxCap)),
    `${index < 4 ? "big" : ""} ${pair.change < 0 ? "negative" : ""}`
  ]);
  return `<div class="heatmap">${data.map(([a, b, c, heat, cls]) => `<div class="heat-cell ${cls}" style="--heat:${heat}"><strong>${a}</strong><span>${b}</span><span>${c}</span></div>`).join("")}</div>`;
}

function tabButtons(name, tabs, active) {
  return `<div class="tabs">${tabs.map(([value, label]) => `<button class="tab ${active === value ? "is-active" : ""}" data-action="tab" data-tab="${name}" data-value="${value}">${label}</button>`).join("")}</div>`;
}

function topMovers() {
  const sorted = [...pairs].sort((a, b) => (state.topMoverTab === "losers" ? a.change - b.change : state.topMoverTab === "volume" ? pairVolumeUsd(b) - pairVolumeUsd(a) : b.change - a.change));
  return `
    <div class="table-shell">
      <table>
        <thead><tr><th>#</th><th>Symbol</th><th>Price</th><th>24H %</th><th>Volume</th></tr></thead>
        <tbody>${sorted.slice(0, 5).map((pair, index) => `<tr><td>${index + 1}</td><td>${pairMarkup(pair)}</td><td>${money(pair.price)}</td><td class="${pair.change >= 0 ? "text-good" : "text-bad"}">${signedPercent(pair.change)}</td><td>${money(pairVolumeUsd(pair))}</td></tr>`).join("")}</tbody>
      </table>
    </div>
  `;
}

function futuresSpot() {
  return `
    <div class="table-shell">
      <table>
        <thead><tr><th>Symbol</th><th>Spot 24H %</th><th>Perp Bias</th><th>Basis</th><th>Funding</th></tr></thead>
        <tbody>${pairs.slice(0, 5).map((pair) => {
          const bias = asNumber(pair.basis) + asNumber(pair.funding);
          return `<tr><td>${pairMarkup(pair)}</td><td class="${pair.change >= 0 ? "text-good" : "text-bad"}">${signedPercent(pair.change)}</td><td class="${bias >= 0 ? "text-good" : "text-bad"}">${bias >= 0 ? "Long" : "Short"}</td><td class="${pair.basis >= 0 ? "text-good" : "text-bad"}">${signedPercent(pair.basis, 2)}</td><td class="${pair.funding >= 0 ? "text-good" : "text-bad"}">${pair.funding.toFixed(4)}%</td></tr>`;
        }).join("")}</tbody>
      </table>
    </div>
  `;
}

function marketAnalytics() {
  const total = Math.max(pairs.length, 1);
  const advance = pairs.filter((pair) => pair.change > 0.05).length;
  const decline = pairs.filter((pair) => pair.change < -0.05).length;
  const neutral = Math.max(0, pairs.length - advance - decline);
  const advancePct = (advance / total) * 100;
  const declinePct = (decline / total) * 100;
  const neutralPct = (neutral / total) * 100;
  const chartPairs = pairs.slice(0, 8);
  const analyticsPairs = chartPairs.length ? chartPairs : [{ key: "N/A", symbol: "N/A", volatility: 0, impact: 0 }];
  return `
    <div class="form-grid">
      <div>
        <div class="panel-title" style="margin-bottom:8px">Market Breadth</div>
        <div class="bar-track"><div class="bar-fill" style="--bar:${advancePct}%;background:linear-gradient(90deg,var(--green),rgba(49,208,107,.52))"></div></div>
        <div style="display:flex;justify-content:space-between;margin-top:6px;font-size:12px"><span class="text-good">Advance ${formatNumber(advancePct, 0)}%</span><span class="text-bad">Decline ${formatNumber(declinePct, 0)}%</span><span class="text-warn">Neutral ${formatNumber(neutralPct, 0)}%</span></div>
      </div>
      <div>
        <div class="panel-title" style="margin-bottom:8px">Volatility by Pair</div>
        ${lineChart([{ values: analyticsPairs.map((pair) => asNumber(pair.volatility) * 100), color: palette.blue }, { values: analyticsPairs.map((pair) => asNumber(pair.impact) * 100), color: palette.amber }], { compact: true, labels: analyticsPairs.map(tokenFromPair), badge: `${formatNumber(average(analyticsPairs, "volatility") * 100, 2)}%` })}
      </div>
      <div>
        <div class="panel-title" style="margin-bottom:8px">Volume Leaders (B USDT)</div>
        ${barChart([...pairs].sort((a, b) => pairVolumeUsd(b) - pairVolumeUsd(a)).slice(0, 6).map((pair) => ({ label: tokenFromPair(pair), value: Number((pairVolumeUsd(pair) / 1_000_000_000).toFixed(2)), color: pair.change >= 0 ? palette.green : palette.red })), { compact: true, horizontal: true })}
      </div>
      <div>
        <div class="panel-title" style="margin-bottom:8px">Market Cap Share</div>
        ${barChart([...pairs].sort((a, b) => pairMarketCapUsd(b) - pairMarketCapUsd(a)).slice(0, 6).map((pair) => ({ label: tokenFromPair(pair), value: Number(((pairMarketCapUsd(pair) / Math.max(pairs.reduce((sum, item) => sum + pairMarketCapUsd(item), 0), 1)) * 100).toFixed(2)), color: palette.blue })), { compact: true, horizontal: true })}
      </div>
    </div>
  `;
}

function priceTrendCards() {
  return `<div class="grid quad-panels">${pairs.slice(0, 4).map((pair, index) => `
    <article class="insight-card">
      <div class="price-card-head">${pairMarkup(pair)}</div>
      <span class="price-card-change ${pair.change >= 0 ? "text-good" : "text-bad"}">${signedPercent(pair.change)}</span>
      <strong>${money(pair.price)}</strong>
      ${sparkline(priceSeriesFromChange(pair, index), pair.change >= 0 ? palette.green : palette.red, true)}
    </article>
  `).join("")}</div>`;
}

function fundingDonut() {
  const total = Math.max(pairs.length, 1);
  const positive = pairs.filter((pair) => pair.funding > 0.0005).length;
  const negative = pairs.filter((pair) => pair.funding < -0.0005).length;
  const neutral = Math.max(0, pairs.length - positive - negative);
  const positivePct = (positive / total) * 100;
  const negativePct = (negative / total) * 100;
  const neutralPct = Math.max(0, 100 - positivePct - negativePct);
  const avgFunding = pairs.length ? pairs.reduce((sum, pair) => sum + asNumber(pair.funding), 0) / pairs.length : 0;
  return `
    <div class="donut-wrap">
      ${donut([{ value: positivePct, color: palette.green }, { value: negativePct, color: palette.red }, { value: neutralPct, color: palette.amber }], `${pairs.length}<br>Total Pairs`)}
      <div class="legend">
        ${legendRow("Positive", `${positive} (${formatNumber(positivePct, 1)}%)`, palette.green)}
        ${legendRow("Negative", `${negative} (${formatNumber(negativePct, 1)}%)`, palette.red)}
        ${legendRow("Neutral", `${neutral} (${formatNumber(neutralPct, 1)}%)`, palette.amber)}
        <div style="margin-top:10px"><span class="field-label">Avg Funding (Selected)</span><strong class="${avgFunding >= 0 ? "text-good" : "text-bad"}" style="font-size:20px">${avgFunding.toFixed(4)}%</strong></div>
      </div>
    </div>
  `;
}

function marketCapSeries() {
  const data = pairs.slice(0, 8).map(pairMarketCapUsd);
  return data.length ? data : values(20, 8, 0.4);
}

function volumeSeries(type = "spot") {
  const data = pairs.slice(0, 8).map((pair) => type === "futures" ? pairFuturesVolumeUsd(pair) : pairVolumeUsd(pair));
  return data.length ? data : values(21, 8, 0.38);
}

function priceSeriesFromChange(pair, index = 0) {
  const current = asNumber(pair.price);
  const change = asNumber(pair.change);
  const start = current / (1 + change / 100 || 1);
  return Array.from({ length: 28 }, (_, step) => {
    const t = step / 27;
    const curve = Math.sin(t * Math.PI * 2 + index) * current * 0.0008;
    return Math.max(0.00000001, start + (current - start) * t + curve);
  });
}

function renderLiquidity() {
  const kpis = state.kpis || {};
  const avgSpread = kpis.averageSpread ?? (pairs.length ? average(pairs, "spread") : 0);
  const maxSpread = kpis.maxSpread ?? (pairs.length ? Math.max(...pairs.map((pair) => asNumber(pair.spread))) : 0);
  const bidDepth = kpis.bidDepthTop10 ?? pairs.reduce((sum, pair) => sum + asNumber(pair.bidDepth), 0);
  const askDepth = kpis.askDepthTop10 ?? pairs.reduce((sum, pair) => sum + asNumber(pair.askDepth), 0);
  const topOfBookDepth = kpis.topOfBookDepth ?? pairs.reduce((sum, pair) => sum + pairBestBid(pair) * pairBidQty(pair) + pairBestAsk(pair) * pairAskQty(pair), 0);
  const slippageEstimate = kpis.slippageEstimate ?? (pairs.length ? average(pairs, "slippage") : 0);
  const liquidityScore = kpis.liquidityScore ?? (pairs.length ? average(pairs, "liquidity") : 0);
  const resilience = kpis.orderBookResilience ?? (pairs.length ? average(pairs, "resilience") : 0);
  const chartPairs = pairs.slice(0, 8);
  const chartLabels = chartPairs.length ? chartPairs.map(tokenFromPair) : ["-"];
  const slippageCurve = state.slippageCurve.length
    ? state.slippageCurve
    : [10000, 50000, 100000, 500000, 1000000].map((size) => ({ orderSize: size, slippage: slippageEstimate * (size / 100000) }));
  const curveLabels = slippageCurve.map((point) => point.orderSize >= 1_000_000 ? `${formatNumber(point.orderSize / 1_000_000, 0)}M` : `${formatNumber(point.orderSize / 1000, 0)}K`);
  const rows = pairs.map((pair) => {
    const depthRatio = asNumber(pair.askDepth) > 0 ? asNumber(pair.bidDepth) / asNumber(pair.askDepth) : 0;
    const status = pair.liquidity >= 85 ? "Very High" : pair.liquidity >= 70 ? "High" : pair.liquidity >= 55 ? "Medium" : "Low";
    return `
    <tr>
      <td>${pairMarkup(pair)}</td><td class="text-good">${pair.spread.toFixed(6)}%</td><td>${compact(pair.bidDepth)}</td><td>${compact(pair.askDepth)}</td>
      <td class="${pair.slippage < 0.03 ? "text-good" : pair.slippage < 0.08 ? "text-warn" : "text-bad"}">${pair.slippage.toFixed(4)}%</td><td>${statusBadge(status)}</td>
      <td class="${depthRatio >= 1 ? "text-good" : "text-bad"}">${depthRatio.toFixed(2)}</td><td>${scoreRing(Math.round(pair.liquidity))}</td>
    </tr>
  `;
  });
  return `
    <div class="grid kpi-grid">
      ${kpiCard({ title: "Average Spread", value: avgSpread.toFixed(6), unit: "%", delta: `${state.timeframe} snapshot`, color: palette.blue, series: chartPairs.map((pair) => asNumber(pair.spread)) })}
      ${kpiCard({ title: "Max Spread", value: maxSpread.toFixed(6), unit: "%", delta: `${state.timeframe} snapshot`, direction: "bad", color: palette.blue, series: chartPairs.map((pair) => asNumber(pair.maxSpread || pair.spread)) })}
      ${kpiCard({ title: "Bid Depth (Top 10)", value: compact(bidDepth), unit: "USDT", delta: `${pairs.length} pairs`, color: palette.green, series: chartPairs.map((pair) => asNumber(pair.bidDepth)) })}
      ${kpiCard({ title: "Ask Depth (Top 10)", value: compact(askDepth), unit: "USDT", delta: `${pairs.length} pairs`, color: palette.green, series: chartPairs.map((pair) => asNumber(pair.askDepth)) })}
      ${kpiCard({ title: "Top-of-Book Depth", value: compact(topOfBookDepth), unit: "USDT", delta: "best bid/ask size", color: palette.green, series: chartPairs.map((pair) => pairBestBid(pair) * pairBidQty(pair) + pairBestAsk(pair) * pairAskQty(pair)) })}
      ${kpiCard({ title: "Slippage Estimate", value: slippageEstimate.toFixed(4), unit: "%", delta: slippageEstimate < 0.03 ? "Low" : slippageEstimate < 0.08 ? "Medium" : "High", direction: slippageEstimate < 0.03 ? "good" : "bad", color: slippageEstimate < 0.03 ? palette.green : palette.red, series: chartPairs.map((pair) => asNumber(pair.slippage)) })}
      ${kpiCard({ title: "Liquidity Score", value: Math.round(liquidityScore), unit: liquidityScore >= 85 ? "Very High" : liquidityScore >= 70 ? "High" : liquidityScore >= 55 ? "Medium" : "Low", delta: "", color: liquidityScore >= 70 ? palette.green : liquidityScore >= 55 ? palette.amber : palette.red, extra: miniGauge(liquidityScore, liquidityScore >= 70 ? palette.green : liquidityScore >= 55 ? palette.amber : palette.red) })}
      ${kpiCard({ title: "Order Book Resilience", value: resilience.toFixed(2), unit: resilience >= 0.75 ? "High" : resilience >= 0.55 ? "Medium" : "Low", delta: "", color: resilience >= 0.75 ? palette.green : resilience >= 0.55 ? palette.amber : palette.red, extra: miniGauge(resilience * 100, resilience >= 0.75 ? palette.green : resilience >= 0.55 ? palette.amber : palette.red) })}
    </div>
    <div class="grid liquidity-layout">
      ${panel("Liquidity Overview (By Pair)", `<div class="table-shell"><table><thead><tr><th>Symbol</th><th>Spread %<br>(Avg)</th><th>Bid Depth Top 10<br>(USDT)</th><th>Ask Depth Top 10<br>(USDT)</th><th>Slippage Est.<br>(100K USDT)</th><th>Liquidity Status</th><th>Depth Imbalance<br>(Bid / Ask)</th><th>Liquidity Score</th></tr></thead><tbody>${rows.join("")}</tbody></table></div>`)}
      <div class="grid">
        ${panel("Spread Snapshot (%)", lineChart([{ values: chartPairs.map((pair) => asNumber(pair.spread)), color: palette.blue }], { compact: true, badge: `${avgSpread.toFixed(6)}%`, labels: chartLabels }), `<select class="mini-select"><option>Avg Spread</option></select>`)}
        ${panel("Depth Snapshot (Top 10)", lineChart([{ values: chartPairs.map((pair) => asNumber(pair.bidDepth)), color: palette.green, fill: true }, { values: chartPairs.map((pair) => asNumber(pair.askDepth)), color: palette.red, fill: true }], { compact: true, labels: chartLabels }), `<select class="mini-select"><option>Total Depth</option></select>`)}
        ${panel("Slippage Curve (vs Order Size)", lineChart([{ values: slippageCurve.map((point) => asNumber(point.slippage)), color: palette.blue }], { compact: true, labels: curveLabels, badge: `${slippageEstimate.toFixed(4)}%` }), `<button class="secondary-button">vs 100K USDT</button>`)}
      </div>
    </div>
    <div class="grid quad-panels">
      ${panel("Pair-by-Pair Liquidity Comparison (Top 10)", scatterLiquidity())}
      ${panel("Order Book Depth Distribution", stackedBars())}
      ${panel("Depth Imbalance Distribution", barChart(pairs.slice(0, 8).map((pair) => ({ label: tokenFromPair(pair), value: Number((asNumber(pair.imbalance) * 100).toFixed(2)), color: pair.imbalance >= 0 ? palette.green : palette.red })), { compact: true, hasNegative: true, showValues: true }))}
      ${panel("Liquidity Insights", liquidityInsights())}
    </div>
    ${footerStatus(`Data Source: ${state.exchange}`, `Source status: ${state.sourceStatus}`, `${pairs.length} active pairs`, `Last update: ${nowLabel()} (UTC+7)`)}
  `;
}

function scatterLiquidity() {
  const width = 520;
  const height = 250;
  const maxSpread = Math.max(...pairs.map((pair) => asNumber(pair.spread)), 0.001);
  const maxDepth = Math.max(...pairs.map((pair) => asNumber(pair.bidDepth) + asNumber(pair.askDepth)), 1);
  const dots = pairs.map((pair, index) => {
    const totalDepth = asNumber(pair.bidDepth) + asNumber(pair.askDepth);
    const x = 48 + (asNumber(pair.spread) / maxSpread) * 360;
    const y = 208 - (totalDepth / maxDepth) * 170;
    const color = pair.liquidity > 75 ? palette.green : pair.liquidity > 55 ? palette.amber : palette.red;
    return `<circle cx="${x}" cy="${y}" r="${7 + pair.liquidity / 20}" fill="${color}" opacity=".9"></circle><text x="${x + 12}" y="${y + 4}" fill="#dfeefe" font-size="11">${pair.symbol.split("/")[0]}</text>`;
  }).join("");
  return `<div class="chart"><svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none"><path d="M42 18V218H500" fill="none" stroke="rgba(150,186,219,.22)"></path><path d="M42 150H500M42 84H500M150 18V218M270 18V218M390 18V218" fill="none" stroke="rgba(150,186,219,.11)" stroke-dasharray="3 5"></path>${dots}<text x="260" y="240" text-anchor="middle" fill="#9db2c9" font-size="11">Spread % (Avg)</text><text x="8" y="110" fill="#9db2c9" font-size="11" transform="rotate(-90 8 110)">Total Depth</text></svg></div>`;
}

function stackedBars() {
  const rows = pairs
    .slice(0, 8)
    .map((pair) => ({
      label: tokenFromPair(pair),
      value: Number(((asNumber(pair.bidDepth) + asNumber(pair.askDepth)) / 1_000_000).toFixed(2)),
      color: asNumber(pair.bidDepth) >= asNumber(pair.askDepth) ? palette.green : palette.red
    }));
  return barChart(rows, { horizontal: true, compact: true });
}

function liquidityInsights() {
  const kpis = state.kpis || {};
  const avgSpread = kpis.averageSpread ?? (pairs.length ? average(pairs, "spread") : 0);
  const liquidityScore = kpis.liquidityScore ?? (pairs.length ? average(pairs, "liquidity") : 0);
  const slippage = kpis.slippageEstimate ?? (pairs.length ? average(pairs, "slippage") : 0);
  const weakest = pairs.length ? pairs.reduce((a, b) => asNumber(a.liquidity) < asNumber(b.liquidity) ? a : b) : null;
  const depthBias = pairs.reduce((sum, pair) => sum + asNumber(pair.imbalance), 0);
  return `
    <div class="feed">
      ${feedInsight("trend", liquidityScore >= 70 ? "Market liquidity is healthy" : "Liquidity needs attention", `Average liquidity score is ${formatNumber(liquidityScore, 1)}/100 with ${avgSpread.toFixed(6)}% average spread.`, liquidityScore >= 70 ? "good" : "warn")}
      ${feedInsight("shield", depthBias >= 0 ? "Bid depth leads ask depth" : "Ask depth leads bid depth", `Net depth imbalance is ${formatNumber(depthBias, 4)} across ${pairs.length} active pairs.`, depthBias >= 0 ? "info" : "warn")}
      ${feedInsight("bell", weakest ? `Watch ${weakest.symbol}` : "No weak pair detected", weakest ? `${weakest.symbol} has the weakest liquidity score at ${formatNumber(weakest.liquidity, 1)} with ${weakest.slippage.toFixed(4)}% estimated slippage.` : "Selected pairs are within normal liquidity range.", weakest && weakest.liquidity < 60 ? "warn" : "good")}
      ${feedInsight("droplet", slippage < 0.03 ? "Slippage remains low" : "Slippage is elevated", `Average 100K USDT slippage estimate is ${slippage.toFixed(4)}%.`, slippage < 0.03 ? "good" : "warn")}
    </div>
  `;
}

function feedInsight(iconName, title, text, tone) {
  const color = tone === "warn" ? palette.amber : tone === "info" ? palette.blue : palette.green;
  return `<div class="feed-item" style="grid-template-columns:42px auto"><div class="icon-bubble" style="width:34px;height:34px;color:${color};background:${color}24">${icon(iconName)}</div><div><strong>${title}</strong><div class="feed-text">${text}</div></div></div>`;
}

function renderWalls() {
  const wallRows = pairs.slice(0, 8).map((pair) => {
    const buyStatus = pair.buyWall > pair.sellWall ? "STRONG" : pair.buyWall > 10 ? "MODERATE" : "WEAK";
    const sellStatus = pair.sellWall > pair.buyWall ? "STRONG" : pair.sellWall > 10 ? "MODERATE" : "WEAK";
    return `
      <tr>
        <td>${pairMarkup(pair)}</td><td><span class="${buyStatus === "STRONG" ? "text-good" : buyStatus === "MODERATE" ? "text-warn" : "text-bad"}">${buyStatus}</span><br>${compact(pair.bidDepth / 36)} @ ${formatNumber(pair.price * .998, pair.price < 1 ? 4 : 2)}</td>
        <td><span class="${sellStatus === "STRONG" ? "text-good" : sellStatus === "MODERATE" ? "text-warn" : "text-bad"}">${sellStatus}</span><br>${compact(pair.askDepth / 34)} @ ${formatNumber(pair.price * 1.002, pair.price < 1 ? 4 : 2)}</td>
        <td>${Math.round(12 + pair.suspicious / 2)}m ${String(Math.round(pair.liquidity / 2)).padStart(2, "0")}s</td><td>${scoreRing(pair.suspicious)}</td>
        <td class="${pair.buyWall > pair.sellWall ? "text-good" : pair.buyWall < pair.sellWall ? "text-bad" : ""}">${pair.buyWall > pair.sellWall ? "Buy" : pair.buyWall < pair.sellWall ? "Sell" : "Neutral"}</td>
        <td>${statusBadge(pair.liquidity > 70 ? "High" : "Healthy")}</td><td>22:15:16</td>
      </tr>
    `;
  });
  return `
    <div class="grid kpi-grid">
      ${kpiCard({ title: "Buy Wall Count", value: "56", delta: "5 vs 1H ago", color: palette.green, series: values(70, 28, 0.4) })}
      ${kpiCard({ title: "Sell Wall Count", value: "52", delta: "4 vs 1H ago", direction: "bad", color: palette.red, series: values(71, 28, 0.38) })}
      ${kpiCard({ title: "Wall Bias", value: "Buyer Pressure", delta: "0.18 (Buy > Sell)", color: palette.green, extra: miniGauge(73, palette.green) })}
      ${kpiCard({ title: "Average Wall Duration", value: "27m 34s", delta: "4m 12s vs 1H ago", color: palette.blue, series: values(72, 28, 0.28) })}
      ${kpiCard({ title: "Suspicious Score", value: "42", unit: "/100", delta: "8 vs 1H ago", direction: "warn", color: palette.amber, series: values(73, 28, 0.35) })}
      ${kpiCard({ title: "Possible Spoof Alerts", value: "18", delta: "6 vs 1H ago", direction: "bad", color: palette.red, series: values(74, 28, 0.34) })}
      ${kpiCard({ title: "Wall Persistence (Avg)", value: "65", unit: "%", delta: "7% vs 1H ago", color: palette.green, extra: `<div class="bar-track" style="margin-top:18px"><div class="bar-fill" style="--bar:65%"></div></div>` })}
      ${kpiCard({ title: "Wall Activity (24H)", value: "High", delta: "18% vs 1H ago", color: palette.green, extra: barChart([{ label: "", value: 5 }, { label: "", value: 8 }, { label: "", value: 11 }, { label: "", value: 7 }, { label: "", value: 13 }, { label: "", value: 6 }, { label: "", value: 12 }], { compact: true, height: 60 }) })}
    </div>
    <div class="grid dual-panels">
      ${panel("Live Wall Monitor", `<div class="table-shell"><table><thead><tr><th>Symbol</th><th>Buy Wall Status</th><th>Sell Wall Status</th><th>Wall Duration</th><th>Suspicious Score</th><th>Wall Bias</th><th>Liquidity Status</th><th>Last Update</th></tr></thead><tbody>${wallRows.join("")}</tbody></table></div>`)}
      ${panel("Wall Activity Timeline", lineChart([{ values: values(75, 60, 0.36, 0.015), color: palette.green, fill: true }, { values: values(76, 60, 0.32, 0.008), color: palette.red, fill: true }, { values: values(77, 60, 0.24, 0.006), color: palette.amber }], { height: 300 }), `<select class="mini-select"><option>5M</option></select>`)}
    </div>
    <div class="grid quad-panels">
      ${panel("Buy vs Sell Wall Histogram", barChart([{ label: "<10K", value: 34, color: palette.green }, { label: "10K-100K", value: 68, color: palette.green }, { label: "100K-1M", value: 82, color: palette.green }, { label: "1M-10M", value: 46, color: palette.green }, { label: ">10M", value: 18, color: palette.green }], { compact: true, showValues: true }))}
      ${panel("Wall Persistence (by Duration)", lineChart([{ values: [22, 41, 63, 72, 81], color: palette.green }], { compact: true, labels: ["< 1 min", "1 - 5", "5 - 15", "15 - 30", "30+"] }), `<select class="mini-select"><option>All Pairs</option></select>`)}
      ${panel("Suspicious Wall Tracker", suspiciousWallTable(), `<select class="mini-select"><option>All Pairs</option></select>`)}
      ${panel("Order Book Snapshot (BTCUSDT)", orderBookSnapshot(pairs[0]))}
    </div>
  `;
}

function suspiciousWallTable() {
  const rows = [
    ["BTCUSDT", "Sell Wall", "$8.42M", "42s", 78],
    ["ETHUSDT", "Buy Wall", "$5.21M", "38s", 71],
    ["XRPUSDT", "Sell Wall", "$3.17M", "27s", 65],
    ["SOLUSDT", "Buy Wall", "$2.94M", "31s", 63],
    ["DOGEUSDT", "Sell Wall", "$1.68M", "22s", 59]
  ].map((row) => `<tr><td>${row[0]}</td><td class="${row[1].includes("Buy") ? "text-good" : "text-bad"}">${row[1]}</td><td>${row[2]}</td><td>${row[3]}</td><td>${statusBadge(String(row[4]))}</td></tr>`);
  return `<div class="table-shell"><table><thead><tr><th>Symbol</th><th>Wall Type</th><th>Size</th><th>Duration</th><th>Suspicious Score</th></tr></thead><tbody>${rows.join("")}</tbody></table></div><button class="ghost-button" style="margin-top:10px">View All Alerts</button>`;
}

function renderAlerts() {
  const filteredAlerts = alerts.filter((alert) => {
    const [time, severity, symbol, type, trigger, status] = alert;
    const search = state.alertFilters.search.toLowerCase();
    return (
      (state.alertFilters.severity === "All Severities" || severity === state.alertFilters.severity) &&
      (state.alertFilters.status === "All Statuses" || status === state.alertFilters.status) &&
      (state.alertFilters.type === "All Types" || type === state.alertFilters.type) &&
      (!search || `${time} ${severity} ${symbol} ${type} ${trigger} ${status}`.toLowerCase().includes(search))
    );
  });
  const rows = filteredAlerts.map((alert, index) => {
    const pair = pairs.find((p) => p.symbol === alert[2]) || pairs[0];
    return `
      <tr>
        <td>25/05/2025 ${alert[0]}</td><td>${statusBadge(alert[1])}</td><td>${pairMarkup(pair)}</td>
        <td>${alert[3]}</td><td class="${alert[1] === "CRITICAL" ? "text-bad" : alert[1] === "WARNING" ? "text-warn" : "text-info"}">${alert[4]}</td>
        <td>${statusBadge(alert[5])}</td>
        <td>
          <button class="table-button" title="View">${icon("eye")}</button>
          <button class="table-button" title="Acknowledge" data-action="ack-alert" data-index="${index}">${icon("check")}</button>
          <button class="table-button" title="More">${icon("more")}</button>
        </td>
      </tr>
    `;
  });
  return `
    <div class="grid kpi-grid seven">
      ${alertKpi("Critical Alerts", "12", "50% vs 1H ago", "bad", "bell")}
      ${alertKpi("Warning Alerts", "27", "12% vs 1H ago", "warn", "bell")}
      ${alertKpi("Info Alerts", "48", "8% vs 1H ago", "info", "bell")}
      ${alertKpi("Unacknowledged", "34", "34% vs 1H ago", "bad", "bell")}
      ${alertKpi("Acknowledged", "53", "6% vs 1H ago", "good", "check")}
      ${alertKpi("Total Alerts (24H)", "182", "15% vs 24H ago", "violet", "bell")}
      ${panel("Notification Status", `<div class="status-row" style="justify-content:space-around">${icon("file")}${icon("trend")}${icon("grid")}${icon("settings")}</div><div class="text-good" style="text-align:center;margin-top:8px">All systems operational</div>`)}
    </div>
    <div class="grid quad-panels">
      ${panel("Alert Frequency (24H)", lineChart([{ values: values(90, 70, 0.6, 0.01), color: palette.blue, fill: true }], { compact: true, badge: "42 Alerts" }), `<select class="mini-select"><option>24H</option></select>`)}
      ${panel("Severity Distribution (24H)", severityDonut())}
      ${panel("Affected Pairs (Top 10)", barChart(pairs.map((pair, i) => ({ label: pair.symbol.split("/")[0], value: [47, 39, 28, 23, 21, 16, 12, 8][i], color: palette.violet })), { compact: true }))}
      ${panel("Alert Rules Triggered (Top 5)", barChart([
        { label: "Latency High", value: 42, color: palette.cyan },
        { label: "Spread Spike", value: 38, color: palette.cyan },
        { label: "Liquidity Deterioration", value: 33, color: palette.cyan },
        { label: "Suspicious Wall", value: 26, color: palette.cyan },
        { label: "Order Book Imbalance", value: 18, color: palette.cyan }
      ], { compact: true, horizontal: true }))}
    </div>
    <div class="grid alerts-layout">
      ${panel(
        "Alerts Center",
        `
          <div class="alert-toolbar">
            ${filterSelect("severity", ["All Severities", "CRITICAL", "WARNING", "INFO"])}
            ${filterSelect("status", ["All Statuses", "Unacknowledged", "Acknowledged", "Resolved"])}
            ${filterSelect("type", ["All Types", "Latency High", "Spread Spike", "Liquidity Deterioration", "Suspicious Wall", "Order Book Imbalance"])}
            <div class="search-wrap"><input class="input" data-action="alert-search" value="${state.alertFilters.search}" placeholder="Search alerts...">${icon("search")}</div>
          </div>
          <div class="table-shell"><table><thead><tr><th>Time</th><th>Severity</th><th>Symbol</th><th>Alert Type</th><th>Trigger Value</th><th>Status</th><th>Action</th></tr></thead><tbody>${rows.join("")}</tbody></table></div>
          <div class="status-footer"><span>Showing 1 to ${filteredAlerts.length} of 182 alerts</span><div class="status-row"><button class="table-button">&lt;</button><button class="segment is-active">1</button><button class="segment">2</button><button class="segment">3</button><button class="segment">10</button><button class="table-button">&gt;</button></div><select class="mini-select"><option>20 / page</option></select></div>
        `
      )}
      <div class="grid">
        ${panel("Pair-Specific Alert Feed", alertFeed(), `<select class="mini-select"><option>BTC/USDT</option></select>`)}
        <div class="grid dual-panels">
          ${miniWarning("Latency Warnings", "15", "25% vs 1H ago")}
          ${miniWarning("Spread Spike Warnings", "14", "17% vs 1H ago")}
          ${miniWarning("Liquidity Deterioration", "13", "30% vs 1H ago")}
          ${miniWarning("Suspicious Wall Alerts", "9", "13% vs 1H ago")}
        </div>
      </div>
    </div>
  `;
}

function alertKpi(title, value, delta, tone, iconName) {
  const color = tone === "bad" ? palette.red : tone === "warn" ? palette.orange : tone === "info" ? palette.blue : tone === "violet" ? palette.violet : palette.green;
  return `
    <article class="kpi-card">
      <div class="kpi-head"><span></span><span class="info-dot">i</span></div>
      <div style="display:grid;grid-template-columns:52px 1fr;gap:12px;align-items:center">
        <div style="color:${color}">${icon(iconName)}</div>
        <div><div class="field-label">${title}</div><div class="kpi-value">${value}</div><div class="delta ${tone === "bad" ? "bad" : tone === "warn" ? "warn" : "good"}">&nearr; ${delta}</div></div>
      </div>
    </article>
  `;
}

function severityDonut() {
  return `
    <div class="donut-wrap">
      ${donut([{ value: 6.6, color: palette.red }, { value: 14.8, color: palette.orange }, { value: 26.4, color: palette.blue }, { value: 29.1, color: palette.green }, { value: 23.1, color: palette.muted }], "182<br>Total")}
      <div class="legend">
        ${legendRow("Critical", "12 (6.6%)", palette.red)}
        ${legendRow("Warning", "27 (14.8%)", palette.orange)}
        ${legendRow("Info", "48 (26.4%)", palette.blue)}
        ${legendRow("Acknowledged", "53 (29.1%)", palette.green)}
        ${legendRow("Resolved", "42 (23.1%)", palette.muted)}
      </div>
    </div>
  `;
}

function filterSelect(key, options) {
  return `<select class="select" data-action="alert-filter" data-key="${key}">${options.map((option) => `<option ${state.alertFilters[key] === option ? "selected" : ""}>${option}</option>`).join("")}</select>`;
}

function alertFeed() {
  return `
    <div class="feed">
      ${alerts.slice(1, 6).map((alert) => `<div class="feed-item"><div class="feed-time">${alert[0].slice(0, 5)}</div><div class="feed-text">${statusBadge(alert[1])} ${alert[3]}: ${alert[4]}</div></div>`).join("")}
      <button class="ghost-button">View full feed</button>
    </div>
  `;
}

function miniWarning(title, value, delta) {
  return panel(title, `<div class="kpi-value">${value}</div><div class="delta bad">&nearr; ${delta}</div>${sparkline(values(value, 22, 0.3), palette.orange)}`);
}

function renderAnalytics() {
  const rows = pairs.slice(0, 5).map((pair) => `
    <tr><td>${pairMarkup(pair)}</td><td>${pair.spread.toFixed(6)}%</td><td>${pair.volatility.toFixed(4)}%</td><td>${statusBadge(pair.regime)}</td><td class="${pair.ofi >= 0 ? "text-good" : "text-bad"}">${pair.ofi >= 0 ? "+" : ""}${pair.ofi.toFixed(3)}</td><td>${sparkline(values(pair.liquidity, 18, 0.28), pair.ofi >= 0 ? palette.green : palette.red)}</td><td>${pair.slippage.toFixed(4)}%</td><td>${pair.impact.toFixed(3)}%</td><td>${scoreRing(pair.liquidity)}</td><td>${icon("bell")}</td></tr>
  `);
  return `
    <div class="grid kpi-grid">
      ${kpiCard({ title: "Avg Spread (5m)", value: "0.00638", unit: "%", delta: "8.21% vs 1H ago", color: palette.blue, series: values(100, 28, 0.25) })}
      ${kpiCard({ title: "Spread Volatility (5m)", value: "0.0182", unit: "%", delta: "12.47% vs 1H ago", direction: "bad", color: palette.blue, series: values(101, 28, 0.24) })}
      ${kpiCard({ title: "Liquidity Regime", value: "High Liquidity", delta: "Score 78 / 100", color: palette.green, extra: miniGauge(78, palette.green) })}
      ${kpiCard({ title: "Order Flow Imbalance", value: "+0.072", delta: "Buy Dominant", color: palette.green, series: values(102, 28, 0.32) })}
      ${kpiCard({ title: "Slippage p95 (5m)", value: "0.0246", unit: "%", delta: "9.33% vs 1H ago", color: palette.blue, series: values(103, 28, 0.28) })}
      ${kpiCard({ title: "Market Impact (5m)", value: "0.013", unit: "%", delta: "7.11% vs 1H ago", color: palette.blue, series: values(104, 28, 0.2) })}
      ${kpiCard({ title: "Pair Correlation (Avg)", value: "0.68", delta: "Moderate", direction: "warn", color: palette.amber, series: values(105, 28, 0.24) })}
      ${kpiCard({ title: "Quote Refresh Rate", value: "12.6", unit: "/ sec", delta: "15.22% vs 1H ago", color: palette.blue, series: values(106, 28, 0.23) })}
    </div>
    <div class="grid liquidity-layout">
      ${panel("Advanced Analytics Overview", `<div class="table-shell"><table><thead><tr><th>Pair</th><th>Spread (5m)</th><th>Spread Volatility</th><th>Liquidity Regime</th><th>OFI (5m)</th><th>Imbalance Trend</th><th>Slippage p95</th><th>Market Impact</th><th>Liquidity Score</th><th>Alert</th></tr></thead><tbody>${rows.join("")}</tbody></table></div>`)}
      <div class="grid dual-panels">
        ${panel("Spread Volatility Trend", lineChart([{ values: values(107, 42, 0.2), color: palette.blue }, { values: values(108, 42, 0.32), color: palette.violet }, { values: values(109, 42, 0.18), color: palette.amber }], { compact: true }), `<select class="mini-select"><option>5m</option></select>`)}
        ${panel("Order Flow Imbalance", barChart(Array.from({ length: 28 }, (_, i) => ({ label: "", value: Math.round(Math.sin(i / 3) * 11 + (Math.random() - 0.4) * 15), color: Math.sin(i / 3) >= 0 ? palette.green : palette.red })), { compact: true, hasNegative: true }), `<select class="mini-select"><option>5m</option></select>`)}
      </div>
    </div>
    <div class="grid triple-panels">
      ${panel("Pair Correlation Matrix (30m)", correlationMatrix())}
      ${panel("Liquidity Regime Analysis (24H)", regimeAnalysis())}
      ${panel("Slippage Distribution (5m)", slippageDistribution(), `<select class="mini-select"><option>BTC/USDT</option></select>`)}
    </div>
    <div class="grid triple-panels">
      ${panel("Market Microstructure Insights", microstructure())}
      ${panel("Performance Diagnostics (24H)", performanceDiagnostics())}
      ${panel("Scenario Insights", scenarios())}
    </div>
    ${footerStatus("Data Source: Binance API", "All systems operational", "Dashboard autosaves every 30s")}
  `;
}

function correlationMatrix() {
  const labels = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA"];
  const values = [
    [1, .82, .71, .64, .55, .49],
    [.82, 1, .76, .68, .58, .51],
    [.71, .76, 1, .63, .5, .46],
    [.64, .68, .63, 1, .57, .63],
    [.55, .58, .5, .57, 1, .6],
    [.49, .51, .46, .63, .6, 1]
  ];
  return `
    <div class="matrix">
      <div class="matrix-cell head"></div>
      ${labels.map((l) => `<div class="matrix-cell head">${l}</div>`).join("")}
      ${labels.map((row, r) => `<div class="matrix-cell head">${row}</div>${labels.map((_, c) => {
        const v = values[r][c];
        const color = v > .75 ? `rgba(49,208,107,${v})` : v > .55 ? `rgba(255,189,46,${v})` : `rgba(255,77,79,${0.45 + v / 2})`;
        return `<div class="matrix-cell" style="--cell:${color}">${v.toFixed(2)}</div>`;
      }).join("")}`).join("")}
    </div>
  `;
}

function regimeAnalysis() {
  return `
    <div class="status-row" style="margin-bottom:10px">
      ${statusBadge("High Liquidity 64.2%")} ${statusBadge("Normal 26.1%")} ${statusBadge("Fragile 7.3%")} ${statusBadge("Illiquid 2.4%")}
    </div>
    ${lineChart([{ values: values(121, 48, 0.18), color: palette.green, fill: true }, { values: values(122, 48, 0.13), color: palette.amber, fill: true }, { values: values(123, 48, 0.1), color: palette.orange, fill: true }, { values: values(124, 48, 0.08), color: palette.red, fill: true }], { compact: true, labels: ["22:00", "02:00", "06:00", "10:00", "14:00", "18:00", "22:00"] })}
  `;
}

function slippageDistribution() {
  return `
    <div style="display:grid;grid-template-columns:1fr 120px;gap:12px">
      ${barChart(Array.from({ length: 16 }, (_, i) => ({ label: i % 3 === 0 ? `${(i * .02).toFixed(2)}%` : "", value: Math.round(4 + Math.sin(i / 2) * 8 + i), color: palette.blue })), { compact: true })}
      <div class="legend">
        ${legendRow("p50", "0.0094%", palette.blue)}
        ${legendRow("p90", "0.0213%", palette.blue)}
        ${legendRow("p95", "0.0246%", palette.blue)}
        ${legendRow("p99", "0.0412%", palette.blue)}
        ${legendRow("Avg", "0.0127%", palette.blue)}
      </div>
    </div>
  `;
}

function microstructure() {
  const items = [
    ["Order Book Resiliency", "High", "Depth recovers within 280ms (avg)", palette.green],
    ["Queue Position Decay", "0.42 / sec", "Moderate", palette.amber],
    ["Book Pressure (Buy/Sell)", "1.36", "Buy Dominant", palette.green],
    ["Hidden Liquidity Ratio", "17.8%", "Above Average", palette.green],
    ["Toxic Flow Indicator", "Low", "0.18 (z-score)", palette.green],
    ["Trade Cluster Activity", "Elevated", "+22% vs 1H avg", palette.amber]
  ];
  return `<div class="grid triple-panels">${items.map((item, i) => `<article class="insight-card"><h3>${item[0]}</h3><strong style="color:${item[3]}">${item[1]}</strong><p>${item[2]}</p>${sparkline(values(130 + i, 18, 0.2), item[3], true)}</article>`).join("")}</div>`;
}

function performanceDiagnostics() {
  return `
    <div class="grid quad-panels">
      <article class="insight-card"><h3>Realized Spread Capture</h3><strong class="text-good">82.1%</strong><p>6.3% vs 24H ago</p>${sparkline(values(140, 20, .26), palette.blue)}</article>
      <article class="insight-card"><h3>Inventory Turnover</h3><strong>18.7 / day</strong><p>1.9 vs 24H ago</p>${sparkline(values(141, 20, .2), palette.blue)}</article>
      <article class="insight-card"><h3>P&L Attribution</h3>${donut([{ value: 72, color: palette.blue }, { value: 19, color: palette.amber }, { value: 9, color: palette.red }], "")}<strong class="text-good">+0.8423 USDT</strong></article>
      <article class="insight-card"><h3>Fill Quality (p95)</h3><strong>0.0246%</strong><p>9.33% vs 24H ago</p>${sparkline(values(142, 20, .23), palette.blue)}</article>
    </div>
  `;
}

function scenarios() {
  return `
    <div class="scenario-grid">
      <article class="scenario-card" style="border-color:rgba(154,107,255,.35);background:rgba(154,107,255,.12)"><h3 class="text-violet">Volatility Spike</h3><p>Probability <strong>28%</strong></p><p>Spread +34%</p><p>Slippage +22%</p></article>
      <article class="scenario-card" style="border-color:rgba(255,77,79,.35);background:rgba(255,77,79,.1)"><h3 class="text-bad">Liquidity Drought</h3><p>Probability <strong>16%</strong></p><p>Depth -46%</p><p>Impact +38%</p></article>
      <article class="scenario-card" style="border-color:rgba(49,208,107,.35);background:rgba(49,208,107,.1)"><h3 class="text-good">Trend Acceleration</h3><p>Probability <strong>35%</strong></p><p>OFI +0.18</p><p>Impact +27%</p></article>
    </div>
  `;
}

function renderReports() {
  const reportRows = reports.map((report, index) => `
    <tr>
      <td>${icon("file")} ${report[0]}</td><td>${statusBadge(report[1])}</td><td>${report[2]}</td><td>${report[3]}</td><td>${statusBadge(report[4])}</td><td>${report[5]}</td>
      <td><button class="table-button">${icon("eye")}</button><button class="table-button" data-action="export-report" data-report="${index}">${icon("download")}</button><button class="table-button">${icon("more")}</button></td>
    </tr>
  `);
  return `
    <div class="grid kpi-grid">
      ${kpiCard({ title: "Reports Generated", value: "156", delta: "18.2% vs last 30D", color: palette.blue, series: values(150, 28, .33) })}
      ${kpiCard({ title: "Total Exports", value: "892", delta: "24.6% vs last 30D", color: palette.blue, series: values(151, 28, .34) })}
      ${kpiCard({ title: "Avg. Report Size", value: "2.48", unit: "MB", delta: "6.3% vs last 30D", direction: "bad", color: palette.blue, series: values(152, 28, .35) })}
      ${kpiCard({ title: "Data Points Processed", value: "1.28", unit: "B", delta: "31.7% vs last 30D", color: palette.blue, series: values(153, 28, .36) })}
      ${kpiCard({ title: "Delivery Success Rate", value: "99.42", unit: "%", delta: "0.7% vs last 30D", color: palette.green, series: values(154, 28, .3) })}
      ${kpiCard({ title: "Scheduled Reports", value: "23", delta: "4 vs last 30D", color: palette.green, series: values(155, 28, .25) })}
      ${panel("Next Report Delivery", `<div class="kpi-value">02:15:44</div><span>Daily Summary (May 21)</span>`)}
      ${panel("Storage Used", `<div style="display:grid;grid-template-columns:1fr 92px;align-items:center"><div><div class="kpi-value">12.6 <small>GB</small></div><div class="text-good">42% of 30 GB</div></div><div class="progress-ring" style="--progress:42%"></div></div>`)}
    </div>
    <div class="grid report-layout">
      ${panel("Report Center", `<div class="table-shell"><table><thead><tr><th>Report Name</th><th>Type</th><th>Period</th><th>Last Updated</th><th>Status</th><th>Size</th><th>Actions</th></tr></thead><tbody>${reportRows.join("")}</tbody></table></div><div class="status-footer"><span>Showing 1 to 8 of 156 reports</span><div class="status-row"><button class="table-button">&lt;</button><button class="segment is-active">1</button><button class="segment">2</button><button class="segment">3</button><span>...</span><button class="segment">20</button><button class="table-button">&gt;</button></div></div>`)}
      ${panel("Report Preview: Daily Liquidity Summary (May 20, 2025)", reportPreview(), `<button class="secondary-button">Full Preview</button>`)}
    </div>
    <div class="grid report-bottom">
      ${panel("Report Library", reportLibrary())}
      ${panel("Downloaded Files", downloads())}
      ${panel("Scheduled Reports", scheduledReports())}
      ${panel("Performance Snapshot", performanceSnapshot(), tabButtons("report", [["pnl", "PnL (USDT)"], ["return", "Return (%)"]], state.reportTab))}
    </div>
  `;
}

function reportPreview() {
  return `
    <div class="preview-grid">
      <div>
        <h3 class="panel-title">Key Highlights</h3>
        <ul class="highlight-list">
          <li>Total traded volume increased by 12.4% compared to previous day.</li>
          <li>Bid-ask spread improved by 8.7% across major pairs.</li>
          <li>Market depth increased across 78% of tracked pairs.</li>
          <li>No significant inventory risk detected.</li>
        </ul>
      </div>
      ${gauge(78, "Good")}
      <div>
        <h3 class="panel-title">Top Pairs by Depth (USDT)</h3>
        ${["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"].map((label, i) => `<div class="top-pair-row"><span>${label}</span><div class="bar-track"><div class="bar-fill" style="--bar:${92 - i * 14}%"></div></div><span>${["2.58M", "1.99M", "881K", "742K", "631K"][i]}</span></div>`).join("")}
      </div>
    </div>
    <div class="mini-metrics">
      ${miniMetric("Volume (24H)", "$3.62B", "12.4%")}
      ${miniMetric("Avg. Spread", "0.021%", "8.7%")}
      ${miniMetric("Trades", "48,392", "9.8%")}
      ${miniMetric("Unique Pairs", "132", "-")}
    </div>
  `;
}

function miniMetric(label, value, delta) {
  return `<div class="mini-metric"><span>${label}</span><strong>${value}</strong><div class="delta good">&uarr; ${delta}</div>${sparkline(values(value.length, 18, .22), palette.blue)}</div>`;
}

function reportLibrary() {
  return `<div class="library-list">${[
    ["Daily Reports", "61", "May 20, 2025"],
    ["Weekly Reports", "21", "May 19, 2025"],
    ["Monthly Reports", "12", "May 01, 2025"],
    ["Performance Reports", "18", "May 20, 2025"],
    ["Analysis Reports", "17", "May 20, 2025"],
    ["Custom Reports", "27", "May 20, 2025"]
  ].map((row) => `<div class="library-row"><div class="file-meta">${icon("file")}<span>${row[0]}</span></div><span>${row[1]}</span><span>${row[2]}</span></div>`).join("")}</div><button class="ghost-button" style="margin-top:12px">View all libraries</button>`;
}

function downloads() {
  return `<div class="download-list">${[
    ["Daily_Summary_2025-05-20.pdf", "PDF", "2.41 MB", "May 20, 2025 21:46"],
    ["Weekly_Overview_2025-W20.xlsx", "Excel", "6.72 MB", "May 19, 2025 08:31"],
    ["Monthly_Report_April_2025.pdf", "PDF", "12.94 MB", "May 01, 2025 09:16"],
    ["Market_Making_Performance_May.pdf", "PDF", "4.88 MB", "May 20, 2025 18:11"],
    ["Inventory_Exposure_Analysis.csv", "CSV", "3.16 MB", "May 20, 2025 17:06"]
  ].map((row) => `<div class="download-row"><div class="file-meta">${icon("file")}<span>${row[0]}</span></div><span>${row[1]}</span><span>${row[2]}</span><span>${row[3]}</span><button class="table-button">${icon("download")}</button></div>`).join("")}</div><button class="ghost-button" style="margin-top:12px">View all downloads</button>`;
}

function scheduledReports() {
  return `<div class="schedule-list">${[
    ["Daily Liquidity Summary", "Daily", "May 21, 00:30"],
    ["Weekly Market Overview", "Weekly (Mon)", "May 26, 08:30"],
    ["Monthly Performance Report", "Monthly (1st)", "Jun 01, 09:15"],
    ["Inventory Risk Alert", "Daily", "May 21, 07:00"],
    ["Wall Activity Report", "Daily", "May 21, 12:00"]
  ].map((row) => `<div class="schedule-row"><span>${row[0]}</span><span>${row[1]}</span><span>${row[2]}</span><span class="text-good">&bull; Active</span></div>`).join("")}</div><button class="ghost-button" style="margin-top:12px">Manage scheduled reports</button>`;
}

function performanceSnapshot() {
  return `
    <div class="grid dual-panels" style="margin-bottom:8px">
      <div><span class="field-label">Total PnL</span><div class="kpi-value">72,923.87 <small>USDT</small></div><div class="delta good">&uarr; 15.6% vs Apr 01 - Apr 20</div></div>
      <div><span class="field-label">Sharpe Ratio</span><div class="kpi-value">2.18</div><div class="delta good">&uarr; 0.34 vs Apr 01 - Apr 20</div></div>
    </div>
    ${lineChart([{ values: values(160, 36, .55, .08), color: palette.green, fill: true }], { compact: true, labels: ["May 01", "May 05", "May 09", "May 13", "May 17", "May 20"] })}
  `;
}

function renderSettings() {
  return `
    <div class="grid settings-grid">
      ${settingCard("1. Exchange Connections", exchangeConnections())}
      ${settingCard("2. API Source Settings", apiSourceSettings())}
      ${settingCard("3. Refresh & Update Settings", refreshSettings())}
      ${settingCard("4. Threshold Settings", thresholdSettings())}
      ${settingCard("5. Wall Detection Settings", wallDetectionSettings())}
      ${settingCard("6. Suspicious Score Settings", suspiciousSettings())}
      ${settingCard("7. Notification Rules", notificationRules())}
      ${settingCard("8. Theme & Display Preferences", themeSettings())}
      ${settingCard("9. Export Preferences", exportPreferences())}
      ${settingCard("10. User & Account Settings", accountSettings(), "wide")}
      ${settingCard("Save & Apply", saveApply())}
    </div>
  `;
}

function settingCard(title, body, extra = "") {
  return `<section class="setting-card ${extra}"><h2>${title}</h2>${body}</section>`;
}

function exchangeConnections() {
  const exchanges = [
    ["Binance", "Connected", true],
    ["Bybit", "Connected", true],
    ["OKX", "Connected", true],
    ["Kraken", "Disconnected", false],
    ["Gate.io", "Disconnected", false],
    ["MEXC", "Disconnected", false]
  ];
  return `
    <div class="exchange-list">
      ${exchanges.map((exchange) => `<div class="exchange-row"><div class="exchange-meta"><span class="status-dot" style="background:${exchange[2] ? palette.green : palette.red}"></span><span>${exchange[0]}</span></div><span class="${exchange[2] ? "text-good" : "text-bad"}">${exchange[1]}</span><button class="secondary-button">${exchange[2] ? "Manage" : "Connect"}</button></div>`).join("")}
    </div>
    <button class="ghost-button" style="width:100%;margin-top:10px">${icon("plus")} Add Exchange</button>
  `;
}

function apiSourceSettings() {
  return `
    <div class="form-grid">
      ${fieldSelect("Primary Data Source", ["Binance (WebSocket API)", "Bybit (WebSocket API)", "OKX (WebSocket API)"])}
      ${fieldSelect("Fallback Source", ["Bybit (WebSocket API)", "OKX (WebSocket API)", "Kraken (REST API)"])}
      <div><label class="field-label">Data Aggregation</label>${tabButtons("aggregation", [["real", "Real-time"], ["balanced", "Balanced"], ["conservative", "Conservative"]], "real")}</div>
      <div class="form-row"><label>Reconnect on Failure</label>${switchButton("reconnect")}</div>
    </div>
  `;
}

function refreshSettings() {
  return `
    <div class="form-grid">
      <div class="form-row"><label>Auto Refresh</label>${switchButton("refresh")}</div>
      ${fieldSelect("Refresh Interval", ["5 seconds", "10 seconds", "30 seconds", "1 minute"])}
      <div style="height:18px"></div>
      <div class="form-row"><div><strong>Manual Refresh</strong><br><span class="field-label">Update all data now</span></div><button class="secondary-button" data-action="manual-refresh">${icon("refresh")} Refresh Now</button></div>
    </div>
  `;
}

function thresholdSettings() {
  return `
    <div class="form-grid">
      ${fieldInput("Max Spread %", "0.50", "%")}
      ${fieldInput("Min Wall Size (USD)", "100,000", "USDT")}
      ${fieldInput("Imbalance Threshold", "0.30", "30%")}
      ${fieldInput("Low Liquidity Threshold", "0.20", "20%")}
      <button class="secondary-button" style="margin-top:10px">${icon("refresh")} Reset to Default</button>
    </div>
  `;
}

function wallDetectionSettings() {
  return `
    <div class="form-grid">
      ${fieldInput("Min Wall Size (USD)", "100,000", "USDT")}
      ${slider("Wall Persistence", 20, "10 sec")}
      ${slider("Merge Walls Within", 28, "2.0 %")}
      <div class="form-row"><label>Display In Charts</label>${switchButton("wallCharts")}</div>
      <div class="form-row"><label>Show Wall Tags</label>${switchButton("wallTags")}</div>
    </div>
  `;
}

function suspiciousSettings() {
  return `
    <div class="form-grid">
      ${slider("Scoring Sensitivity", 65, "0.65")}
      ${fieldSelect("Score Decay (Half-life)", ["15 minutes", "30 minutes", "1 hour"])}
      ${slider("Min Score to Alert", 60, "60")}
      <div class="form-row"><label>Highlight in UI</label>${switchButton("animations")}</div>
    </div>
  `;
}

function notificationRules() {
  return `
    <div class="form-grid">
      <div class="form-row"><label>Enable Notifications</label>${switchButton("notifications")}</div>
      ${fieldInput("High Suspicious Score", "70", "")}
      ${fieldInput("Large Wall Detected", "100,000", "USDT")}
      ${fieldInput("High Imbalance", "30", "%")}
      ${fieldInput("Low Liquidity", "20", "%")}
      <div class="status-row" style="justify-content:space-around">${icon("file")}${icon("trend")}${icon("bell")}${icon("settings")}</div>
    </div>
  `;
}

function themeSettings() {
  return `
    <div class="form-grid">
      <div><label class="field-label">Theme</label>${tabButtons("theme", [["dark", "Dark"], ["dim", "Dim"], ["midnight", "Midnight"]], "dark")}</div>
      <div><label class="field-label">Accent Color</label><div class="color-swatches">${["blue", "green", "violet", "orange", "red", "cyan", "magenta"].map((color) => `<button class="swatch-button ${state.settings.accent === color ? "is-active" : ""}" style="--swatch:${palette[color]}" data-action="accent" data-value="${color}"></button>`).join("")}</div></div>
      ${fieldSelect("Chart Color Scheme", ["Neon", "Accessible", "Classic"])}
      <div class="form-row"><label>Compact Mode</label>${switchButton("compactMode")}</div>
      <div class="form-row"><label>Show Animations</label>${switchButton("animations")}</div>
    </div>
  `;
}

function exportPreferences() {
  return `
    <div class="form-grid">
      ${fieldSelect("Default Format", ["CSV", "PDF", "Excel"])}
      <div class="form-row"><label>Include Charts</label>${switchButton("includeCharts")}</div>
      <div class="form-row"><label>Include Raw Data</label>${switchButton("includeRaw")}</div>
      <div class="form-row"><label>Compress Exports</label>${switchButton("compressExports")}</div>
    </div>
  `;
}

function accountSettings() {
  return `
    <div class="grid dual-panels">
      <div class="form-grid">
        ${fieldInput("Display Name", "Market Maker", "")}
        ${fieldSelect("Time Zone", ["(UTC+7) Bangkok", "(UTC+0) London", "(UTC-5) New York"])}
        ${fieldSelect("Language", ["English", "Bahasa Indonesia"])}
      </div>
      <div class="form-grid">
        <div class="form-row"><label>Two-Factor Authentication</label>${statusBadge("Enabled")}</div>
        ${fieldSelect("Session Timeout", ["30 minutes", "1 hour", "4 hours"])}
        <div class="form-row"><label>Change Password</label><button class="secondary-button">Change Password</button></div>
      </div>
    </div>
  `;
}

function saveApply() {
  return `
    <p class="field-label">Apply your settings to customize your dashboard experience.</p>
    <button class="primary-button" style="width:100%;margin:8px 0" data-action="save-settings">${icon("check")} Save Changes</button>
    <button class="secondary-button" style="width:100%">${icon("refresh")} Reset All Settings</button>
  `;
}

function fieldInput(label, value, suffix) {
  return `<div class="form-row"><label>${label}</label><div class="input-wrap"><input class="input" value="${value}">${suffix ? `<span style="position:absolute;right:10px;top:50%;transform:translateY(-50%);color:var(--muted)">${suffix}</span>` : ""}</div></div>`;
}

function fieldSelect(label, options) {
  return `<div><label class="field-label">${label}</label><select class="select">${options.map((option) => `<option>${option}</option>`).join("")}</select></div>`;
}

function slider(label, value, display) {
  return `<div class="slider-row"><div><label class="field-label">${label}</label><input type="range" min="0" max="100" value="${value}"></div><input class="input" value="${display}"></div>`;
}

function switchButton(key) {
  return `<button class="switch ${state.settings[key] ? "is-on" : ""}" data-action="toggle-setting" data-key="${key}" aria-label="${key}"></button>`;
}

function renderPage() {
  const pages = {
    overview: renderOverview,
    markets: renderMarkets,
    liquidity: renderLiquidity,
    walls: renderWalls,
    alerts: renderAlerts,
    analytics: renderAnalytics,
    reports: renderReports,
    settings: renderSettings
  };
  return pages[state.page]();
}

function renderApp() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="dashboard">
      <aside class="sidebar">
        <div class="brand-mark" title="Crypto Liquidity">${icon("droplet")}</div>
        <nav class="nav">
          ${navItems.map(([id, label, iconName]) => `<button class="nav-button ${state.page === id ? "is-active" : ""}" data-action="navigate" data-page="${id}">${icon(iconName)}<span>${label}</span></button>`).join("")}
        </nav>
        <button class="collapse-button">&laquo; Collapse</button>
      </aside>
      <main class="main">
        <div class="topbar">
          <div class="title-block">
            <h1>Crypto Liquidity Monitoring Dashboard</h1>
            <p>Market Maker / Liquidity Analysis</p>
          </div>
          <div class="account-bar">
            <button class="icon-button" title="Theme">${icon("sun")}</button>
            <button class="icon-button" title="Notifications">${icon("bell")}</button>
            <div class="user-pill">
              <div class="avatar">MM</div>
              <div><span class="user-name">Market Maker</span><span class="user-status">Online</span></div>
              <span>&#8964;</span>
            </div>
          </div>
        </div>
        ${filterBar()}
        <div class="page-content">${renderPage()}</div>
      </main>
    </div>
    <div id="toast" class="toast"></div>
  `;
}

function filterBar() {
  return `
    <section class="filter-bar">
      <div>
        <label class="field-label">Exchange / Source</label>
        <div class="select-wrap">
          <select class="select" data-action="global-select" data-key="exchange">
            ${["Binance", "Bybit", "OKX", "Kraken", "Gate.io", "MEXC"].map((x) => `<option ${state.exchange === x ? "selected" : ""}>${x}</option>`).join("")}
          </select>
          <span class="chevron">&#8964;</span>
        </div>
      </div>
      <div>
        <label class="field-label">Symbol Group</label>
        <div class="select-wrap">
          <select class="select" data-action="global-select" data-key="symbolGroup">
            ${["Major Pairs", "Layer 1", "DeFi", "Meme", "Custom Watchlist"].map((x) => `<option ${state.symbolGroup === x ? "selected" : ""}>${x}</option>`).join("")}
          </select>
          <span class="chevron">&#8964;</span>
        </div>
      </div>
      <div>
        <label class="field-label">Interval</label>
        ${timeframePicker()}
      </div>
      <div>
        <label class="field-label">Auto Refresh</label>
        <button class="refresh-state" data-action="auto-refresh"><span class="status-dot" style="background:${state.autoRefresh ? palette.green : palette.muted}"></span>${state.autoRefresh ? "ON" : "OFF"}</button>
      </div>
      <div>
        <label class="field-label">Last Update</label>
        <div class="last-update">${icon("clock")} ${nowLabel()} (UTC+7)</div>
      </div>
      <button class="secondary-button" data-action="export-report">${icon("download")} Export Report</button>
    </section>
  `;
}

function timeframePicker() {
  return `
    <div class="timeframe-picker ${state.timeframeMenuOpen ? "is-open" : ""}">
      <button class="timeframe-trigger" data-action="toggle-timeframe-menu" aria-expanded="${state.timeframeMenuOpen ? "true" : "false"}">
        <span>
          <span class="timeframe-kicker">Interval</span>
          <strong>${state.timeframe}</strong>
        </span>
      </button>
      <div class="timeframe-menu">
        <div class="timeframe-favorites">
          ${favoriteTimeframes.map((time) => timeframeOption(time, "favorite")).join("")}
        </div>
        ${timeframeGroups
          .map((group) => `
            <div class="timeframe-section">
              <div class="timeframe-section-title">${group.title}</div>
              <div class="timeframe-options">
                ${group.items.map((time) => timeframeOption(time)).join("")}
              </div>
            </div>
          `)
          .join("")}
      </div>
    </div>
  `;
}

function timeframeOption(time, variant = "") {
  return `<button class="timeframe-option ${variant} ${state.timeframe === time ? "is-active" : ""}" data-action="timeframe" data-value="${time}">${time}</button>`;
}

function legendRow(label, value, color) {
  return `<div class="legend-row"><span class="legend-label"><span class="legend-swatch" style="--swatch:${color}"></span>${label}</span><strong>${value}</strong></div>`;
}

function footerStatus(...items) {
  return `
    <footer class="status-footer">
      <div class="status-row">${items.slice(0, -1).map((item) => `<span><span class="status-dot"></span>${item}</span>`).join("")}</div>
      <span>${items.at(-1) || ""}</span>
    </footer>
  `;
}

function displaySymbolFromKey(symbol) {
  return String(symbol || "").replace("USDT", "/USDT");
}

const defaultWatchlistSymbols = [
  "BTCUSDT",
  "ETHUSDT",
  "SOLUSDT",
  "XRPUSDT",
  "BNBUSDT",
  "ADAUSDT",
  "DOGEUSDT",
  "AVAXUSDT",
  "LINKUSDT",
  "TRXUSDT",
  "DOTUSDT",
  "LTCUSDT"
];

function symbolsForGroup() {
  const groups = {
    "Major Pairs": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"],
    "Layer 1": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "ADAUSDT"],
    DeFi: ["ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT"],
    Meme: ["DOGEUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"],
    "Custom Watchlist": defaultWatchlistSymbols
  };
  return groups[state.symbolGroup] || defaultWatchlistSymbols;
}

function endpointForPage(page) {
  const params = new URLSearchParams({
    exchange: state.exchange,
    interval: state.timeframe
  });
  if (["overview", "markets", "liquidity", "walls", "analytics"].includes(page)) {
    params.set("symbols", symbolsForGroup().join(","));
  }
  if (page === "alerts") {
    const severity = state.alertFilters.severity.replace("All Severities", "all");
    const status = state.alertFilters.status.replace("All Statuses", "all");
    const type = state.alertFilters.type.replace("All Types", "all");
    return `${API_BASE}/alerts?${new URLSearchParams({ exchange: state.exchange, severity, status, type, search: state.alertFilters.search })}`;
  }
  if (page === "reports") return `${API_BASE}/reports?${new URLSearchParams({ exchange: state.exchange })}`;
  if (page === "settings") return `${API_BASE}/settings`;
  return `${API_BASE}/${page}?${params}`;
}

async function fetchDashboardData(page = state.page, options = {}) {
  try {
    const response = await fetch(endpointForPage(page));
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    applyBackendData(page, payload);
    backendWarningShown = false;
    return true;
  } catch (error) {
    if (!options.silent && !backendWarningShown) {
      showToast("Backend unavailable, using local fallback data.");
      backendWarningShown = true;
    }
    return false;
  }
}

function applyBackendData(page, payload) {
  if (!payload || payload.status !== "ok") return;
  state.sourceStatus = payload.sourceStatus;
  state.lastUpdate = payload.lastUpdate ? new Date(payload.lastUpdate) : new Date();
  const data = payload.data || {};
  // Map KPI summary, wall summary, and insights from backend
  state.kpis = data.kpis && typeof data.kpis === "object" ? { ...data.kpis } : {};
  state.wallSummary = data.walls?.summary && typeof data.walls.summary === "object" ? { ...data.walls.summary } : {};
  if (page === "markets") {
    state.marketSummary = data.summary && typeof data.summary === "object" ? { ...data.summary } : {};
  }
  if (page === "liquidity") {
    state.liquidityComparison = Array.isArray(data.comparison) ? data.comparison : [];
    state.slippageCurve = Array.isArray(data.slippageCurve) ? data.slippageCurve : [];
  }
  state.insights = Array.isArray(data.insights) ? data.insights : [];
  if (Array.isArray(data.pairs)) {
    pairs.length = 0;
    data.pairs.forEach((backendPair) => {
      const key = backendPair.key || backendPair.symbol?.replace("/", "");
      const symbol = backendPair.displaySymbol || backendPair.symbol || displaySymbolFromKey(key);
      const target = {
        symbol,
        key,
        coin: String(symbol).split("/")[0].toLowerCase(),
        price: 0,
        change: 0,
        volume: 0,
        marketCap: 0,
        futuresVol: 0,
        oi: 0,
        funding: 0,
        basis: 0,
        spread: 0,
        maxSpread: 0,
        imbalance: 0,
        bidDepth: 0,
        askDepth: 0,
        buyWall: 0,
        sellWall: 0,
        liquidity: 0,
        suspicious: 0,
        slippage: 0,
        resilience: 0,
        regime: "Medium",
        ofi: 0,
        volatility: 0,
        impact: 0
      };
      Object.assign(target, {
        price: backendPair.price ?? target.price,
        change: backendPair.change ?? backendPair.change24h ?? target.change,
        volume: backendPair.volume ?? target.volume,
        marketCap: backendPair.marketCap ?? target.marketCap,
        futuresVol: backendPair.futuresVol ?? target.futuresVol,
        oi: backendPair.oi ?? target.oi,
        funding: backendPair.funding ?? target.funding,
        basis: backendPair.basis ?? target.basis,
        spread: backendPair.spread ?? backendPair.spreadPct ?? target.spread,
        maxSpread: backendPair.maxSpread ?? target.maxSpread,
        imbalance: backendPair.imbalance ?? target.imbalance,
        bidDepth: backendPair.bidDepth ?? target.bidDepth,
        askDepth: backendPair.askDepth ?? target.askDepth,
        liquidity: backendPair.liquidity ?? target.liquidity,
        suspicious: backendPair.suspicious ?? target.suspicious,
        slippage: backendPair.slippage ?? target.slippage,
        resilience: backendPair.resilience ?? target.resilience,
        regime: backendPair.regime ?? target.regime,
        ofi: backendPair.ofi ?? target.ofi,
        volatility: backendPair.volatility ?? target.volatility,
        impact: backendPair.impact ?? target.impact,
        bestBid: backendPair.bestBid ?? target.bestBid,
        bestAsk: backendPair.bestAsk ?? target.bestAsk,
        bidQty: backendPair.bidQty ?? target.bidQty,
        askQty: backendPair.askQty ?? target.askQty,
        bids: backendPair.bids ?? target.bids,
        asks: backendPair.asks ?? target.asks
      });
      pairs.push(target);
    });
  }
  if (data.walls?.byPair) {
    data.walls.byPair.forEach((wallPair) => {
      const target = pairs.find((pair) => pair.key === wallPair.key);
      if (!target) return;
      target.buyWall = wallPair.buyWall ?? target.buyWall;
      target.sellWall = wallPair.sellWall ?? target.sellWall;
      target.suspicious = wallPair.suspicious ?? target.suspicious;
    });
  }
  if (Array.isArray(data.alerts)) {
    alerts.length = 0;
    data.alerts.forEach((alert) => {
      const time = alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString("en-GB", { hour12: false }) : "--:--:--";
      alerts.push([
        time,
        alert.severity || "INFO",
        displaySymbolFromKey(alert.symbol),
        alert.alert_type || alert.alertType || "Market Alert",
        alert.trigger_value || alert.triggerValue || "-",
        alert.status || "Unacknowledged"
      ]);
    });
  }
  if (Array.isArray(data.reports)) {
    reports.length = 0;
    data.reports.forEach((report) => {
      reports.push([
        report.report_type || "Liquidity Report",
        report.file_format || "CSV",
        report.period || state.timeframe,
        report.timestamp || "-",
        report.status || "Completed",
        report.size_bytes ? `${(report.size_bytes / 1024).toFixed(1)} KB` : "-"
      ]);
    });
  }
}

function resolveWebSocketUrl() {
  const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
  const host = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "127.0.0.1:8000"
    : window.location.host;
  return `${protocol}${host}/ws`;
}

function connectWebSocket() {
  window.clearTimeout(wsReconnectTimer);

  socket = new WebSocket(resolveWebSocketUrl());

  socket.onopen = () => {
    backendWarningShown = false;
  };

  socket.onmessage = (event) => {
    if (!state.autoRefresh) return;
    try {
      const payload = JSON.parse(event.data);
      applyBackendData(state.page, payload);
      renderApp();
    } catch (error) {
      console.error("Failed to parse WebSocket payload", error);
    }
  };

  socket.onerror = () => {
    socket.close();
  };

  socket.onclose = () => {
    if (!backendWarningShown) {
      showToast("Backend unavailable, using local fallback data.");
      backendWarningShown = true;
      mutateMarket();
      renderApp();
    }
    // Auto-reconnect: coba sambung ulang dalam 3 detik jika koneksi terputus mendadak.
    wsReconnectTimer = window.setTimeout(connectWebSocket, 3000);
  };
}

async function saveSettingsToBackend() {
  try {
    const response = await fetch(`${API_BASE}/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        selectedExchange: state.exchange,
        autoRefresh: state.autoRefresh,
        refreshInterval: state.timeframe,
        accentColor: state.settings.accent,
        exportPreferences: {
          includeCharts: state.settings.includeCharts,
          includeRawData: state.settings.includeRaw,
          compressExports: state.settings.compressExports
        }
      })
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    showToast("Settings saved successfully.");
  } catch (error) {
    showToast("Backend unavailable, settings kept locally.");
  }
}

async function generateBackendReport(index = 0) {
  const report = reports[index] || reports[0];
  try {
    const response = await fetch(`${API_BASE}/reports/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        exchange: state.exchange,
        reportType: report[0],
        fileFormat: state.settings.includeRaw ? "xlsx" : "csv",
        interval: state.timeframe
      })
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    showToast(`Report generated: ${payload.data.fileName}`);
    await fetchDashboardData("reports", { silent: true });
    renderApp();
  } catch (error) {
    downloadMockReport(index);
  }
}

function showToast(message) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => toast.classList.remove("show"), 2400);
}

function mutateMarket() {
  pairs.forEach((pair) => {
    const move = (Math.random() - 0.45) * 0.0025;
    pair.price *= 1 + move;
    pair.change += (Math.random() - 0.5) * 0.08;
    pair.spread = Math.max(0.003, pair.spread + (Math.random() - 0.5) * 0.0003);
    pair.imbalance = Math.max(-0.3, Math.min(0.3, pair.imbalance + (Math.random() - 0.5) * 0.018));
    pair.bidDepth *= 1 + (Math.random() - 0.48) * 0.012;
    pair.askDepth *= 1 + (Math.random() - 0.52) * 0.012;
  });
  state.lastUpdate = new Date();
}

function downloadMockReport(index = 0) {
  const report = reports[index] || reports[0];
  const payload = {
    report: report[0],
    generatedAt: new Date().toISOString(),
    exchange: state.exchange,
    timeframe: state.timeframe,
    summary: {
      averageSpread: average(pairs, "spread"),
      totalBidDepth: pairs.reduce((sum, pair) => sum + pair.bidDepth, 0),
      totalAskDepth: pairs.reduce((sum, pair) => sum + pair.askDepth, 0),
      alerts: alerts.length
    }
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${report[0].replaceAll(" ", "_").toLowerCase()}_mock.json`;
  link.click();
  URL.revokeObjectURL(url);
  showToast("Mock report exported.");
}

document.addEventListener("click", (event) => {
  const clickedPicker = event.target.closest(".timeframe-picker");
  const target = event.target.closest("[data-action]");
  if (!target) {
    if (state.timeframeMenuOpen && !clickedPicker) {
      state.timeframeMenuOpen = false;
      renderApp();
    }
    return;
  }
  const action = target.dataset.action;
  if (action === "navigate") {
    state.page = target.dataset.page;
    state.timeframeMenuOpen = false;
    renderApp();
    window.scrollTo({ top: 0, behavior: "smooth" });
    fetchDashboardData(state.page).then(() => renderApp());
  }
  if (action === "toggle-timeframe-menu") {
    state.timeframeMenuOpen = !state.timeframeMenuOpen;
    renderApp();
  }
  if (action === "timeframe") {
    state.timeframe = target.dataset.value;
    state.timeframeMenuOpen = false;
    state.overviewPage = 1;
    state.lastUpdate = new Date();
    renderApp();
    fetchDashboardData(state.page).then(() => renderApp());
  }
  if (action === "auto-refresh") {
    // Toggle ini sekarang mengatur apakah update real-time dari WebSocket
    // diterapkan ke UI atau tidak; koneksi WS sendiri tetap terbuka.
    state.autoRefresh = !state.autoRefresh;
    state.timeframeMenuOpen = false;
    renderApp();
  }
  if (action === "overview-page") {
    const page = Number(target.dataset.page);
    if (Number.isFinite(page)) state.overviewPage = page;
    state.timeframeMenuOpen = false;
    renderApp();
  }
  if (action === "tab") {
    if (target.dataset.tab === "topMover") state.topMoverTab = target.dataset.value;
    if (target.dataset.tab === "futures") state.futuresTab = target.dataset.value;
    if (target.dataset.tab === "report") state.reportTab = target.dataset.value;
    state.timeframeMenuOpen = false;
    renderApp();
  }
  if (action === "toggle-setting") {
    const key = target.dataset.key;
    state.settings[key] = !state.settings[key];
    renderApp();
  }
  if (action === "save-settings") {
    saveSettingsToBackend();
  }
  if (action === "manual-refresh") {
    fetchDashboardData(state.page).then((ok) => {
      if (!ok) mutateMarket();
      renderApp();
      showToast("Market data refreshed.");
    });
  }
  if (action === "accent") {
    state.settings.accent = target.dataset.value;
    document.documentElement.style.setProperty("--blue", palette[state.settings.accent] || palette.blue);
    renderApp();
  }
  if (action === "ack-alert") {
    const visibleIndex = Number(target.dataset.index);
    if (alerts[visibleIndex]) alerts[visibleIndex][5] = "Acknowledged";
    renderApp();
    showToast("Alert acknowledged.");
  }
  if (action === "export-report") {
    generateBackendReport(Number(target.dataset.report || 0));
  }
});

document.addEventListener("change", (event) => {
  const target = event.target.closest("[data-action]");
  if (!target) return;
  const action = target.dataset.action;
  if (action === "global-select") {
    state[target.dataset.key] = target.value;
    state.timeframeMenuOpen = false;
    state.overviewPage = 1;
    state.lastUpdate = new Date();
    renderApp();
    fetchDashboardData(state.page).then(() => renderApp());
  }
  if (action === "alert-filter") {
    state.alertFilters[target.dataset.key] = target.value;
    renderApp();
    fetchDashboardData("alerts").then(() => renderApp());
  }
});

document.addEventListener("input", (event) => {
  const target = event.target.closest("[data-action='alert-search']");
  if (!target) return;
  state.alertFilters.search = target.value;
  renderApp();
  fetchDashboardData("alerts", { silent: true }).then(() => renderApp());
});

renderApp();
fetchDashboardData(state.page, { silent: true }).then(() => renderApp());
connectWebSocket();