# CargoVision AI — Deployment Preflight & Eligibility Verification

**Date:** October 21, 2026  
**Auditor:** DevOps & Systems Architecture  
**Project Path:** `C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI`  
**Target Repository:** `https://github.com/ayushcmd/CargoVision-AI`  
**Target Branch:** `cargovision-main`  
**Budget Constraint:** **Strictly ₹0.00 / month ($0.00 USD) — No credit card or paid subscriptions**

---

## 1. Hosting Eligibility & Cost Correction

### 1.1 Hugging Face Spaces Policy Correction
> [!WARNING]
> **Correction of Unsupported Claim:** Earlier deployment guides assumed Hugging Face offered free CPU Basic hardware for custom Docker Spaces. Direct account inspection on the Hugging Face Spaces creation dashboard confirms that **Docker Spaces are now locked behind a paid PRO subscription ($9.00 USD / month ≈ ₹751 INR / month)** and require a mandatory credit card.
>
> In accordance with the strictly ₹0 / month budget, **Hugging Face Spaces Docker is marked UNSUPPORTED for this deployment**.

---

### 1.2 Verified Genuinely Free Hosting Architecture (Strictly ₹0 / Month)

To satisfy the 744 MB peak RAM requirement without triggering OOM crashes or requiring credit card verification:

| Layer | Recommended Free Technology | Hardware / Specification | Credit Card Required? | Monthly Cost (USD) | Monthly Cost (INR)* |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Frontend UI** | **Cloudflare Pages** | Pure React 19 SPA (`dist/`), Global Edge CDN, Unlimited Bandwidth | **NO** | **$0.00** | **₹0.00** |
| **Backend API** | **Local Host via Cloudflare Tunnel (`cloudflared`)** | Native PC (16 GB RAM, 5.09 FPS CPU, zero OOM risk, all 8 models local) | **NO** | **$0.00** | **₹0.00** |
| **Alternative Backend** | **Google Colab / Kaggle Cloud Runner** | Free Cloud VM (12-16 GB RAM, optional T4 GPU) via tunnel | **NO** | **$0.00** | **₹0.00** |
| **Source Control** | **GitHub (`ayushcmd`)** | Branch `cargovision-main` (Code + 8 models tracked) | **NO** | **$0.00** | **₹0.00** |
| **Total Recurring Cost** | — | — | — | **$0.00 / mo** | **₹0.00 / mo** |

*\* Exchange rate used: 1 USD ≈ 83.50 INR as of October 2026. Zero credit card or paid subscriptions required.*

---

## 2. Technical Feasibility Breakdown

### 2.1 Why Free Cloud Container Tiers Fail for CargoVision AI
- **Render Free Tier:** 512 MB RAM ceiling. CargoVision AI idle footprint with models is **579.80 MB**, causing immediate `SIGKILL / exit code 137` on startup.
- **Koyeb / Railway:** 512 MB RAM ceiling. Koyeb also places a $29 credit card authorization hold.
- **PythonAnywhere:** 512 MB total disk, no ASGI / FastAPI support, no PyTorch wheel support.
- **Google Cloud Run / AWS / Oracle:** Free tier compute is technically sufficient, but all require an active credit card with identity holds during registration.

### 2.2 Why Cloudflare Tunnel + Cloudflare Pages Succeeds
- **100% Free & No Credit Card:** Cloudflare Pages is completely free for static SPAs. Cloudflare Tunnel (`cloudflared`) is completely free and requires zero payment details.
- **Memory Safety:** Runs on the host machine's 16 GB RAM. The 744 MB peak memory usage utilizes <5% of host memory, guaranteeing 0% risk of OOM termination.
- **Performance:** CPU inference runs at 5.09 FPS with zero cold starts and zero container build timeouts.
- **Model Checkpoints:** All 8 models are already downloaded, verified, and active on disk.

---

## 3. GitHub Authentication & Repository Status

### 3.1 Authenticated Account Verification
- **Command:** `gh auth status`
- **Verification Result:** Active GitHub account is confirmed as **`ayushcmd`**.

### 3.2 Repository & Branch Status
- **Repository URL:** `https://github.com/ayushcmd/CargoVision-AI`
- **Branch `cargovision-main`:** Synchronized with `origin/cargovision-main` (commit `8dd9bbe`).
- **Models Tracked in Git:** 8 checkpoints (147.78 MB total). All individual files are below 65.5 MB, avoiding Git LFS pointer failures and bandwidth quotas.

---

## 4. Required Environment Variables

### 4.1 Backend Configuration (FastAPI)
| Variable Name | Required | Recommended Value | Description |
| :--- | :---: | :--- | :--- |
| `ENV` | Yes | `production` | Enables production security defaults |
| `HOST` | Yes | `127.0.0.1` | Binds to local loopback interface (Cloudflare Tunnel forwards to it) |
| `PORT` | Yes | `8000` | Local port exposed to tunnel |
| `MAX_UPLOAD_SIZE_MB` | Yes | `35` | Maximum upload size ceiling |
| `MAX_CONCURRENT_JOBS`| Yes | `1` | Enforces single-job concurrency on CPU |
| `CORS_ORIGINS` | Yes | `https://*.pages.dev,http://localhost:5173` | Allows requests from Cloudflare Pages domain |

### 4.2 Frontend Configuration (Vite)
| Variable Name | Required | Example Value | Description |
| :--- | :---: | :--- | :--- |
| `VITE_API_BASE_URL` | Yes | `https://<tunnel-subdomain>.trycloudflare.com` | Public HTTPS tunnel URL pointing to the backend |

> [!WARNING]
> Never store sensitive keys or secrets in variables prefixed with `VITE_`, as they are bundled into the public JavaScript output.

---

## 5. Security & Action Checklist

- [x] All 8 computer vision models verified on disk and in Git.
- [x] Backend verified locally (`http://127.0.0.1:8000/health` -> HTTP 200 OK).
- [x] Frontend verified locally (`npm run build` succeeds in 29.4s).
- [x] Security test suite passed (`deployment/test_security.py` -> 5/5 passed).
- [x] Hardcoded Roboflow API keys in `train_numbers.py` and `train_yolo.py` sanitized to `os.environ.get("ROBOFLOW_API_KEY", "")`.
- [ ] **Next Action:** User approves deploying frontend to Cloudflare Pages and launching Cloudflare Tunnel for public backend access.
