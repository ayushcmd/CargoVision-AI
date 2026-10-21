# CargoVision AI — Production Deployment Runbook (Zero-Cost Architecture)

**Target Architecture:** Cloudflare Pages (Public Frontend SPA) + Cloudflare Tunnel to Host Backend (or Colab Cloud Runner)  
**Total Cost:** Strictly $0.00 / month (₹0.00 INR) — Zero Credit Card Required  
**Project Path:** `C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI`  
**Git Branch:** `cargovision-main`  

---

## 1. Overview of Zero-Cost Production Architecture

```
[Public Visitor / Mobile Browser]
        │
        ▼ (HTTPS / Edge CDN)
[Cloudflare Pages: https://cargovision-ai.pages.dev]
  - Static React 19 SPA (dist/)
  - Hosted 24/7 at $0 cost on Cloudflare's global edge network
  - Reads: VITE_API_BASE_URL=https://<tunnel-id>.trycloudflare.com
        │
        ▼ (Encrypted HTTPS Tunnel over WebSocket / HTTP2)
[Cloudflare Tunnel: https://<tunnel-id>.trycloudflare.com]
  - Free Quick Tunnel (Zero login, zero credit card)
        │
        ▼ (Local loopback: http://127.0.0.1:8000)
[CargoVision AI Backend Engine (Host PC)]
  - FastAPI ASGI on Python 3.11
  - 16 GB host RAM (>20x headroom for 744 MB peak inference)
  - Full local speed: 5.09 FPS on CPU
  - Pre-warmed YOLOv8 + NAFNet + EasyOCR + FPDF2 PDF Generator
```

---

## 2. Phase 1 — Deploy Public Frontend to Cloudflare Pages

### Step 1.1: Deploy via Cloudflare Dashboard (Recommended)
1. Log in to [dash.cloudflare.com](https://dash.cloudflare.com).
2. Go to **Workers & Pages** -> **Create application** -> **Pages** -> **Connect to Git**.
3. Select your repository: `ayushcmd/CargoVision-AI`.
4. Configure build settings:
   - **Project Name:** `cargovision-ai`
   - **Production Branch:** `cargovision-main`
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Build Output Directory:** `dist`
5. Click **Save and Deploy**. Cloudflare will build and publish your frontend to:
   `https://cargovision-ai.pages.dev`

### Step 1.2: Alternative Deploy via Wrangler CLI
```powershell
cd C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI\frontend
npm run build
npx wrangler pages deploy dist --project-name cargovision-ai
```

---

## 3. Phase 2 — Expose Backend via Cloudflare Tunnel (`cloudflared`)

Cloudflare provides a lightweight, free tunnel binary (`cloudflared`) that securely exposes your local backend (`127.0.0.1:8000`) over an encrypted public HTTPS URL without port forwarding, router configuration, or a credit card.

### Step 2.1: Download `cloudflared` (One-Time Setup)
Download the official standalone executable from Cloudflare:
```powershell
# In PowerShell:
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI\cloudflared.exe"
```

### Step 2.2: Ensure Local Backend is Running
Ensure the local FastAPI backend is active on port 8000:
```powershell
cd "C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI\full model\src\api"
& "C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI\.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000
```
Verify health:
```powershell
curl.exe http://127.0.0.1:8000/health
# Returns: {"status":"healthy", ...}
```

### Step 2.3: Start the Free Public Tunnel
Open a separate terminal window and launch the tunnel:
```powershell
.\cloudflared.exe tunnel --url http://127.0.0.1:8000
```
`cloudflared` will generate a public HTTPS URL in the console, for example:
```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
|  https://railway-inspection-vision.trycloudflare.com                                       |
+--------------------------------------------------------------------------------------------+
```

### Step 2.4: Test the Public Tunnel Endpoint
Test from any computer or mobile phone:
```powershell
curl.exe https://railway-inspection-vision.trycloudflare.com/health
```

---

## 4. Phase 3 — Connect Frontend to Backend Tunnel

1. Go to your **Cloudflare Pages** dashboard -> `cargovision-ai` -> **Settings** -> **Environment variables**.
2. Set variable:
   - **Variable Name:** `VITE_API_BASE_URL`
   - **Value:** `https://railway-inspection-vision.trycloudflare.com` *(your public tunnel URL)*
3. Trigger a redeploy (or deploy updated `.env.production` if using CLI).

---

## 5. Phase 4 — Cloud Runner Alternative (Google Colab / Kaggle)

If you need the backend to stay online while away from your primary computer:

1. Create a free notebook on [Google Colab](https://colab.research.google.com) or [Kaggle](https://www.kaggle.com).
2. Run the following cell:
   ```python
   # Clone production branch
   !git clone -b cargovision-main https://github.com/ayushcmd/CargoVision-AI.git
   %cd CargoVision-AI

   # Install CPU dependencies
   !pip install -r deployment/requirements.txt
   !wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared && chmod +x cloudflared

   # Launch backend and expose public tunnel
   import subprocess
   subprocess.Popen(["python", "run.py"])
   !./cloudflared tunnel --url http://localhost:7860
   ```
3. Copy the printed `*.trycloudflare.com` URL into Cloudflare Pages `VITE_API_BASE_URL`.

---

## 6. End-to-End Verification & Troubleshooting

### Verification Checklist:
- [ ] Open `https://cargovision-ai.pages.dev` in a web browser.
- [ ] Verify live metrics cards (Wagons Processed, Detection Confidence, Processing FPS).
- [ ] Upload a test railway video (`Assests/wagon_number_detection2.mp4`).
- [ ] Confirm wagon bounding boxes render in real time.
- [ ] Confirm 11-digit wagon number is parsed and checksum validated.
- [ ] Download the generated PDF inspection report.

### Troubleshooting:
- **Tunnel URL Changed on Restart:** Free `trycloudflare.com` URLs regenerate each time the command is restarted. For a permanent custom subdomain at $0 cost, add your free domain to Cloudflare and create a named tunnel (`cloudflared tunnel create cargovision`).
- **HTTP 429 Too Many Requests:** Working as intended. `MAX_CONCURRENT_JOBS=1` protects hardware by serializing video inference.
