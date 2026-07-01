# Crypto Liquidity Monitoring Dashboard

Dashboard web untuk memantau kondisi pasar crypto, likuiditas order book, wall activity, alert, analytics, dan report untuk kebutuhan market making.

Aplikasi ini terdiri dari frontend HTML/CSS/JavaScript murni dan backend FastAPI. Backend mengambil data market dari exchange publik, menghitung metrik likuiditas, menyimpan snapshot ke SQLite, lalu menyajikan dashboard melalui API dan static frontend.

## Tech Stack

| Bagian | Teknologi |
| --- | --- |
| Frontend | HTML, CSS, JavaScript murni |
| Backend | Python, FastAPI, Uvicorn |
| Database | SQLite dengan `aiosqlite` |
| Data source | Public REST API exchange dan fallback mock generator |
| Report export | CSV/XLSX dengan `pandas` dan `openpyxl` |

## Fitur Utama

- Overview market maker dengan KPI spread, depth, imbalance, wall bias, slippage, dan liquidity score.
- Market dashboard untuk market cap, volume, top movers, heatmap, futures/spot bias, funding bias, dan tabel pair aktif.
- Liquidity monitoring berbasis order book top levels.
- Wall detection untuk buy wall, sell wall, persistence, dan suspicious score.
- Alert generation untuk spread spike, imbalance, low liquidity, dan suspicious wall.
- Analytics untuk market impact, volatility, liquidity regime, dan scenario view.
- Report generation ke CSV/XLSX.
- Settings dashboard untuk refresh interval, threshold, notification rule, dan export preference.
- Fallback data lokal ketika exchange API lambat atau tidak tersedia.

## Struktur Folder Penting

```text
.
|-- backend/
|   |-- api/                 # FastAPI route handlers
|   |-- exchange/            # Adapter Binance, Bybit, OKX, Gate.io, Kraken, MEXC
|   |-- services/            # Market, liquidity, wall, alert, analytics, report logic
|   |-- data/market_data.db  # SQLite database
|   |-- generated_reports/   # Output report CSV/XLSX
|   |-- main.py              # FastAPI app entrypoint
|   |-- database.py          # SQLite schema and query helpers
|   `-- requirements.txt
|-- frontend/
|   |-- index.html
|   |-- app.js
|   `-- styles.css
|-- run_backend.bat          # Bootstrap venv, install dependencies, run server
`-- README.md
```

Beberapa folder/file lama terkait SIGA masih ada di repository, tetapi aplikasi dashboard crypto saat ini berjalan dari `backend/` dan `frontend/`.

## Cara Menjalankan

### Opsi cepat di Windows

Dari root project:

```powershell
.\run_backend.bat
```

Script tersebut akan:

1. Masuk ke folder `backend/`.
2. Membuat virtual environment di `backend/.venv` jika belum ada.
3. Menginstall dependency dari `backend/requirements.txt`.
4. Menjalankan FastAPI dengan Uvicorn di `127.0.0.1:8000`.

Buka dashboard di browser:

```text
http://127.0.0.1:8000/
```

### Opsi manual

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Lalu buka:

```text
http://127.0.0.1:8000/
```

## API Utama

Semua endpoint utama berada di prefix `/api`.

| Endpoint | Keterangan |
| --- | --- |
| `GET /api/health` | Health check backend, database, frontend, collector, dan source status |
| `GET /api/overview` | KPI overview, pairs, wall summary, alert summary, dan insight |
| `GET /api/markets` | Market summary, top movers, pairs, volume, market cap |
| `GET /api/liquidity` | Liquidity KPI, comparison, slippage curve |
| `GET /api/walls` | Wall detection dan wall summary |
| `GET /api/alerts` | Daftar alert dan summary alert |
| `GET /api/analytics` | Analytics summary dan scenario data |
| `GET /api/reports` | Daftar report yang sudah dibuat |
| `POST /api/reports/generate` | Generate report CSV/XLSX |
| `GET /api/settings` | Ambil setting dashboard |
| `PUT /api/settings` | Update setting dashboard |
| `POST /api/settings/reset` | Reset setting ke default |

Contoh:

```powershell
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/api/overview?exchange=Binance&interval=5m&symbols=BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT"
```

## Exchange yang Didukung

- Binance
- Bybit
- OKX
- Gate.io
- Kraken
- MEXC

Pilihan exchange tersedia di filter dashboard. Jika data real tidak lengkap atau API exchange gagal, backend akan memakai fallback mock data agar dashboard tetap bisa berjalan.

## Database

Database menggunakan SQLite:

```text
backend/data/market_data.db
```

Schema dibuat otomatis saat startup backend. Data yang disimpan meliputi:

- Market snapshots
- Order book snapshots
- Wall detections
- Alerts
- Analytics summary
- Settings

## Report

Report dibuat melalui menu Reports atau endpoint:

```text
POST /api/reports/generate
```

Output report disimpan di:

```text
backend/generated_reports/
```

Format yang didukung:

- CSV
- XLSX

## Frontend

Frontend tidak memakai framework seperti React, Vue, atau Next.js. Semua UI dirender dari:

```text
frontend/app.js
frontend/styles.css
frontend/index.html
```

Backend menyajikan frontend sebagai static files, jadi tidak perlu menjalankan dev server frontend terpisah.

## Troubleshooting

### Port 8000 sudah dipakai

Matikan proses yang memakai port tersebut, atau jalankan Uvicorn di port lain:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### Data exchange lambat atau fallback

Cek endpoint health:

```powershell
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/api/health"
```

Jika `sourceStatus` adalah `fallback` atau `partial_real`, kemungkinan exchange API sedang lambat, rate limited, atau tidak bisa dijangkau.

### Dependency belum terpasang

Jalankan ulang:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Status Saat Ini

- Overview dan Markets sudah disesuaikan agar memakai data backend aktif.
- Backend FastAPI dan SQLite sudah berjalan.
- Frontend disajikan langsung dari backend.
- Beberapa bagian menu lain masih bisa terus dirapikan agar seluruh angka demo lama diganti dengan data backend.
