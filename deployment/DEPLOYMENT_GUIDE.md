# CargoVision AI — Public Demo Deployment & Operations Guide

This guide provides step-by-step procedures for deploying **CargoVision AI** to production hosting platforms while maintaining 100% compatibility with local Windows development.

---

## 1. Local Development Workflow (Preserved)

The standard local development workflow remains completely functional:

### Backend Startup
```powershell
# In PowerShell from project root:
cd "C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI\full model\src\api"
& "..\..\..\.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- Local API URL: `http://127.0.0.1:8000`
- API Health Status: `http://127.0.0.1:8000/health`
- Swagger Documentation: `http://127.0.0.1:8000/docs`

### Frontend Startup
```powershell
# In a separate PowerShell session:
cd "C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI\frontend"
npm run dev -- --host 127.0.0.1 --port 5173
```
- Local Web Interface: `http://127.0.0.1:5173`

---

## 2. Environment Variables Specification

All environment variables have built-in defaults that enable local execution out-of-the-box. For cloud deployments, configure the following variables:

| Variable | Target | Description | Default / Example |
| :--- | :--- | :--- | :--- |
| `HOST` | Backend | IP interface to bind Uvicorn | `127.0.0.1` (local) / `0.0.0.0` (cloud) |
| `PORT` | Backend | Port to listen on | `8000` (local) / `7860` (Hugging Face) |
| `ENV` | Backend | Runtime environment tag | `development` / `production` |
| `CORS_ORIGINS` | Backend | Comma-separated allowed frontend domains | `http://localhost:5173,http://127.0.0.1:5173` |
| `VITE_API_BASE_URL` | Frontend | Target backend API base URL | `http://localhost:8000` |
| `DATABASE_PATH` | Backend | Custom path for SQLite database | `full model/detection/inspections.db` |
| `UPLOAD_DIR` | Backend | Directory for uploaded videos | `full model/Video` |
| `MODEL_DIR` | Backend | Override directory for model weights | Unset (uses project tree) |
| `MAX_UPLOAD_SIZE_MB` | Backend | Maximum allowed video upload size | `35` (in megabytes) |
| `MAX_CONCURRENT_JOBS` | Backend | Concurrency ceiling to protect container RAM | `1` (for CPU demo) |

> [!CAUTION]
> Frontend variables starting with `VITE_` are bundled directly into client-side JavaScript. **Never put API keys or secrets in `VITE_` variables.**

---

## 3. Recommended Deployment Option A: Hugging Face Spaces + Cloudflare Pages (100% Free Tier)

This architecture provides **16 GB RAM** for zero cost, completely preventing the Out-Of-Memory (OOM) crashes that occur on 512 MB free tiers.

### Step 1: Deploy Backend to Hugging Face Spaces
1. Log in to [Hugging Face](https://huggingface.co/) and click **New Space**.
2. Space Settings:
   - **Space Name:** `cargovision-ai-backend`
   - **License:** `mit` or `apache-2.0`
   - **SDK:** Select **Docker** (Blank)
   - **Hardware:** Select **CPU Basic (2 vCPU, 16 GB RAM) - Free**
3. Push the repository (containing `Dockerfile`, `full model/`, `wagon number detection/`, and `deployment/requirements.txt`) to the Space Git repository:
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/cargovision-ai-backend
   git push hf main
   ```
4. In Space **Settings** -> **Variables and Secrets**, set:
   - `CORS_ORIGINS`: `https://cargovision-ai.pages.dev` (your frontend domain)
   - `MAX_UPLOAD_SIZE_MB`: `35`
   - `MAX_CONCURRENT_JOBS`: `1`
5. Your public backend will be available at:
   `https://YOUR_USERNAME-cargovision-ai-backend.hf.space`

### Step 2: Deploy Frontend to Cloudflare Pages or Vercel
1. In Cloudflare Dashboard, go to **Workers & Pages** -> **Create application** -> **Pages**.
2. Connect your frontend repository or use Direct Upload.
3. Build Settings:
   - **Framework preset:** `Vite`
   - **Root directory:** `frontend`
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
4. Set Environment Variable:
   - `VITE_API_BASE_URL`: `https://YOUR_USERNAME-cargovision-ai-backend.hf.space`
5. Deploy. The landing page and inspection app will be instantly live on global CDN with 0s cold start.

---

## 4. Fallback Deployment Option B: Render or Railway (PaaS)

If using a commercial PaaS provider:

### Render (Starter Tier - $7/month)
1. In [Render Dashboard](https://dashboard.render.com/), create a **New Web Service**.
2. Select **Docker Runtime** and choose **Starter Plan (1 GB RAM, 1 vCPU)**.
   *(Do not select the 512 MB Free tier; the models require ~744 MB during inference).*
3. Add Environment Variables:
   - `PORT`: `10000`
   - `CORS_ORIGINS`: `https://YOUR-FRONTEND-URL`
   - `MAX_UPLOAD_SIZE_MB`: `25`
   - `MAX_CONCURRENT_JOBS`: `1`
4. Configure Health Check Path: `/health`

### Railway (Usage-based - ~$5/month)
1. In [Railway](https://railway.app/), create a **New Project from GitHub Repo**.
2. Railway automatically detects the `Dockerfile`.
3. In Service Settings -> **Variables**:
   - `PORT`: `${{PORT}}`
   - `CORS_ORIGINS`: `https://YOUR-FRONTEND-URL`
4. Set Service Memory Limit to **1.5 GB** or **2 GB** for comfortable concurrency headroom.

---

## 5. Local Docker Container Testing

To test the container locally on your workstation before pushing to cloud:

```bash
# 1. Build the Docker image
docker build -t cargovision-ai:local .

# 2. Run the container locally (mapped to host port 8000)
docker run -p 8000:7860 \
  -e PORT=7860 \
  -e CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173" \
  cargovision-ai:local

# 3. Test container health
curl http://localhost:8000/health
```

---

## 6. Data Retention, Backups & Maintenance

1. **Inspection History Persistence:**
   - In cloud containers without persistent volume mounts, the SQLite database resides in `/app/data/detection/inspections.db` and is ephemeral (resets on container redeployment).
   - For long-term portfolio showcase, keep sample inspections pre-seeded or mount a persistent volume (e.g. Render Persistent Disk or Fly.io Volume).
2. **Temporary Video Cleanup:**
   - Uploaded videos in `/app/data/Video` should be periodically pruned. A daily cron job or startup cleaner can delete videos older than 48 hours.
3. **Rollback Strategy:**
   - If an update fails, redeploy the previous Docker image tag or git commit on the hosting platform. Local code remains independent and untouched.
