# Render.com Deployment Guide for Crypto Market Maker

## Prerequisites

1. **GitHub Repository**: ✅ Already done (`davisbagus47-stack/crypto-market-maker`)
2. **Render Account**: Create at https://render.com (free tier available)
3. **Docker**: ✅ Already configured with `Dockerfile`

## Step-by-Step Deployment

### 1. Create Render Account

1. Go to https://render.com
2. Click **"Sign up"**
3. Choose **"Sign up with GitHub"**
4. Authorize Render to access your GitHub repositories

### 2. Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Select repository: `davisbagus47-stack/crypto-market-maker`
3. Click **"Connect"**

### 3. Configure Service

Fill in the following:

| Field | Value |
|-------|-------|
| **Name** | `crypto-market-maker` |
| **Environment** | `Docker` |
| **Plan** | `Starter` (free) or `Standard` |
| **Branch** | `main` |
| **Dockerfile path** | `./Dockerfile` |

### 4. Environment Variables (Optional)

Add these in Render dashboard under **Environment**:

```
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
PORT=8000
```

### 5. Add Persistent Disk

For SQLite database persistence:

1. Scroll to **"Disks"**
2. Click **"Add Disk"**
3. Configure:
   - **Name**: `data`
   - **Mount Path**: `/app/backend/data`
   - **Size**: 1 GB (free tier)

### 6. Deploy

1. Click **"Create Web Service"**
2. Wait for build to complete (usually 3-5 minutes)
3. You'll get a URL like: `https://crypto-market-maker-xxxx.onrender.com`

## Verify Deployment

After deployment completes:

```bash
# Test health check
curl https://crypto-market-maker-xxxx.onrender.com/api/health

# Access frontend
https://crypto-market-maker-xxxx.onrender.com

# Test API
curl https://crypto-market-maker-xxxx.onrender.com/api/overview
```

## Auto-Deploy on Push

Render automatically redeploys when you push to `main` branch. To disable:

1. Go to service settings
2. Disable **"Auto-deploy"** toggle

## Troubleshooting

### Build fails
- Check **Logs** tab in Render dashboard
- Ensure `Dockerfile` exists at root of repo
- Verify `backend/requirements.txt` has correct packages

### Port issues
- Render exposes port 8000 automatically from Dockerfile
- Don't change port configuration

### Database not persisting
- Verify disk is mounted at `/app/backend/data`
- Check **Disks** section shows correct mount path

### App keeps restarting
- Check service logs for errors
- Verify health check endpoint (`/api/health`) is working
- Check that all API dependencies are in `requirements.txt`

## Pricing

- **Starter (Free tier)**: 
  - 0.5 vCPU, 512 MB RAM
  - Auto-spins down after 15 min of inactivity
  - 1 GB storage
  
- **Standard**: 
  - Full resources
  - Always running
  - Paid tier

## Custom Domain (Optional)

To use custom domain like `crypto.yourdomain.com`:

1. Go to service settings → **Custom Domain**
2. Add your domain
3. Update DNS records as instructed
4. Wait for SSL certificate (usually instant)

## Support

- Render Docs: https://render.com/docs
- GitHub: https://github.com/davisbagus47-stack/crypto-market-maker
- Check service logs in Render dashboard for debugging

---

**Your deployed app URL**: `https://crypto-market-maker-xxxx.onrender.com` (after deploy)
