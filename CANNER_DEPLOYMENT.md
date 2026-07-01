# Crypto Market Maker - Canner Deployment Guide

## Deployment Configuration

### What is Canner?
Canner is a cloud platform for deploying containerized applications. It handles building, deploying, and scaling your Docker containers.

### Prerequisites
- GitHub repository (✅ Already done: `davisbagus47-stack/crypto-market-maker`)
- Canner account (create at https://canner.io or similar platform)
- Docker knowledge (optional - Canner handles Docker builds)

### Deployment Steps

#### 1. Connect GitHub Repository to Canner

1. Go to https://canner.io (or your Canner platform)
2. Sign in with GitHub
3. Click **"New Project"** or **"Add Repository"**
4. Select `davisbagus47-stack/crypto-market-maker`
5. Authorize Canner to access your repository

#### 2. Configure Deployment Settings

Create/update these environment variables in Canner dashboard:

```
PORT=8000
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

#### 3. Set Port and Health Check

- **Port**: `8000`
- **Health Check URL**: `/api/health`
- **Health Check Interval**: 30 seconds

#### 4. Configure Database Persistence

For SQLite database persistence:

- **Volumes/Mount Path**: `/app/backend/data` → persistent volume on Canner
- This ensures your `market_data.db` survives container restarts

#### 5. Deploy

1. Click **"Deploy"** in Canner dashboard
2. Monitor build logs
3. Once deployed, get your public URL: `https://your-app-name.canner.app` (or similar)

### Verify Deployment

After deployment, test these endpoints:

```bash
# Health check
curl https://your-app-name.canner.app/api/health

# API endpoints
curl https://your-app-name.canner.app/api/overview
curl https://your-app-name.canner.app/api/markets

# Frontend
https://your-app-name.canner.app
```

### Environment Variables for Production

If needed, add these to Canner dashboard:

```
DATABASE_URL=sqlite:///./backend/data/market_data.db
LOG_LEVEL=INFO
CORS_ORIGINS=*
```

### Troubleshooting

**Build fails**: Check that `Dockerfile` exists and `backend/requirements.txt` is valid
**Port issues**: Ensure port 8000 is exposed in Dockerfile ✅ (already done)
**Database errors**: Make sure `/app/backend/data` volume is mounted

### Support

- Canner Documentation: https://docs.canner.io
- This project GitHub: https://github.com/davisbagus47-stack/crypto-market-maker
