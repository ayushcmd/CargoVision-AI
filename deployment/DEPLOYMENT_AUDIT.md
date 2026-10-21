# CargoVision AI — Public Demo Hosting & Deployment Feasibility Audit

**Project:** CargoVision AI (Intelligent Railway Wagon Inspection System)  
**Location:** `C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI`  
**Date:** 2026-10-21  
**Status:** Completed Feasibility Audit & Measurement

---

## 1. Executive Summary

This feasibility audit evaluates the infrastructure, compute, memory, storage, security, and financial requirements for deploying **CargoVision AI** to a publicly accessible, portfolio-quality demonstration.

### Key Empirical Findings
1. **Model Footprint:** The complete suite of 8 project checkpoints totals **147.78 MB** (0.144 GB). Downloaded EasyOCR weights (`craft_mlt_25k.pth` and `english_g2.pth`) add **93.74 MB**, bringing the **grand total model footprint to 241.52 MB**.
2. **Measured RAM Consumption (Empirical):**
   - Base Python Process: `34.41 MB`
   - Post-Imports (Torch, Ultralytics, EasyOCR): `315.58 MB`
   - All Models Loaded in Memory: `579.79 MB`
   - Single Image End-to-End Inference: `682.14 MB`
   - 30-Frame Video Cascaded Inference Peak: **`744.13 MB`**
3. **Critical Hosting Constraint:** Any free-tier hosting plan with a **512 MB RAM ceiling (such as Render Free Tier)** will trigger an immediate **Out-Of-Memory (OOM) SIGKILL** when loading the models. A minimum of **1.0 GB RAM** is required for CPU execution, and **2.0 GB+ RAM** is recommended for concurrent stability.
4. **Processing Throughput (CPU Only):** The cascaded inference pipeline operates at **5.09 FPS** on standard CPU. For a typical 5–10 second demo video (150–300 frames), end-to-end processing requires approximately **30–60 seconds**.
5. **Recommended Architecture:**
   - **Primary (Zero Cost / High Memory):** Backend on **Hugging Face Spaces** (Docker SDK, Free Tier provides **2 vCPU, 16 GB RAM**, 50 GB storage) paired with Frontend on **Cloudflare Pages / Vercel** (Free Tier). Estimated cost: **$0.00 / month**.
   - **Fallback (Commercial Managed PaaS):** Unified or split deployment on **Render Starter** (1 GB RAM, $7/month ≈ ₹585/mo) or **Railway Hobby** (1–2 GB RAM, ~$5/month ≈ ₹415/mo).

---

## 2. Model Inventory & Resource Specifications

Every checkpoint utilized by the CargoVision AI cascaded pipeline was audited, hashed, and measured:

| Model Role | File Path | Format / Arch | Size | SHA-256 (Prefix) | CPU Memory | Runtime Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Wagon Detector (Model A)** | `full model/railway_hackathon_take6/merged_model_v6_generalized/weights/best.pt` | YOLOv8s | 21.48 MB | `7a38038bcdf8078c` | ~65 MB | Required; loaded on pipeline start |
| **Wagon Number Detector (Model B v2)** | `wagon number detection/wnd/models/WNDEModelV2.pt` | YOLOv8n | 5.94 MB | `e195613f09b78d82` | ~25 MB | Required; runs on wagon crops |
| **Wagon Number Detector (Model B v1)** | `full model/railway_hackathon_numbers/number_detector_v1/weights/best.pt` | YOLOv8s | 21.47 MB | `7d2860d8e45d411a` | ~65 MB | Local alternative checkpoint |
| **Damage Detector (Model C)** | `full model/railway_hackathon_damage/damage_detector_v1/weights/best.pt` | YOLOv8s | 21.48 MB | `15857853c9a5bee0` | ~65 MB | Required; runs on wagon crops |
| **Deblur Engine (NAFNet)** | `full model/NAFnet/NAFNet-GoPro-width32.pth` | NAFNet width=32 | 65.49 MB | `19394e6155d12ef6` | ~190 MB | Optional/Adaptive; runs on blurry crops |
| **Low-Light Enhancer (Zero-DCE)** | `full model/zero_dce_model/Epoch99.pth` | Zero-DCE | 0.05 MB | `ca8855b90df9a80f` | ~2 MB | Optional; night frame enhancement |
| **EasyOCR Text Detector** | `~/.EasyOCR/model/craft_mlt_25k.pth` | CRAFT | 79.30 MB | `863cdb73f80c657e` | ~110 MB | Cached on first execution |
| **EasyOCR Recognizer** | `~/.EasyOCR/model/english_g2.pth` | ResNet+BiLSTM | 14.44 MB | `74ee5d142b7813a0` | ~45 MB | Cached on first execution |

**Total Checkpoint Footprint:** **241.52 MB**  
All models execute cleanly in CPU-only mode (`torch.device('cpu')`). No GPU hardware is strictly mandatory for demonstration purposes.

---

## 3. Measured Resource Consumption Budget

All measurements were empirically gathered using `psutil` on the active Python 3.11 virtual environment processing representative Indian Railways freight captures:

```
Process Memory Growth Timeline:
[Initial Process]   34.41 MB
        │
[Imports Loaded]   315.58 MB  (+281.17 MB: PyTorch, Torchvision, OpenCV, Ultralytics, EasyOCR)
        │
[Models Loaded]    579.79 MB  (+264.21 MB: Model A, Model B, Model C, NAFNet, EasyOCR)
        │
[Image Inference]  682.14 MB  (+102.35 MB: Forward passes, intermediate feature maps)
        │
[Video Peak RSS]   744.13 MB  (Cascaded tracking, multi-frame crop buffers, video decoding)
```

### Detailed Resource Matrix

| Operation | Wall-Clock Time | Peak RSS Memory | CPU Utilization | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Python Imports** | 12.37 s | 315.58 MB | 1 Core (~100%) | Heavy initialization of PyTorch and EasyOCR |
| **Model Weight Loading** | 5.16 s | 579.79 MB | 1 Core (~100%) | Loading PyTorch state dicts from disk to RAM |
| **Single Image Pipeline** | 1.82 s | 682.14 MB | Multi-thread (2-4 cores) | Model A (536ms) + Model B + OCR |
| **Video Processing (30 frames)** | 5.89 s | 744.13 MB | Multi-thread (~3 cores) | Effective throughput: **5.09 FPS** |
| **Full Video (150 frames, 5s)** | ~29.5 s | 744.13 MB | Sustained ~75% CPU | Memory stabilizes, no unbounded memory leaks |
| **PDF Report Generation** | 0.18 s | Negligible (<5 MB) | Single thread | In-memory stream generation via FPDF |

---

## 4. Hosting Architecture Evaluation

### Option A — Static Frontend + Decoupled Hosted Backend (Recommended)
- **Frontend:** React + TypeScript + Vite deployed on **Cloudflare Pages**, **Vercel**, or **Netlify**.
  - *Pros:* 100% free, global CDN edge caching, 0ms cold start for landing/documentation, independent CI/CD build.
  - *Cons:* Requires cross-origin resource sharing (CORS) between frontend and backend domains.
- **Backend:** FastAPI container hosted on **Hugging Face Spaces (Docker SDK)** or **Render Starter**.
  - *Pros:* Decoupled compute; backend can scale, restart, or sleep without breaking the landing page UI.

### Option B — Single Unified Container (All-in-One)
- Frontend built statically and served by FastAPI (`app.mount("/", StaticFiles(directory="frontend/dist", html=True))`) inside a single Docker container.
  - *Pros:* Eliminates CORS configuration entirely; single URL, single deployment artifact.
  - *Cons:* Cold starts affect the entire website (user sees a loading spinner when visiting the URL); larger container image (~1.5 GB with Node build stage).

### Option C — Split Public Demo (Curated Sample Video + Live Inspection)
- Provide pre-computed sample inspections (e.g. `wagon_number_detection2.mp4`) for instantaneous preview, while still supporting live custom uploads with server-side size limits (e.g. max 25 MB, max 15 seconds).
  - *Pros:* Eliminates user frustration during cold starts; provides immediate portfolio showcase value.
  - *Cons:* Requires maintaining sample database fixtures in the repository.

### Option D — GPU-Accelerated Cloud Instance
- AWS `g4dn.xlarge` (T4 GPU) or RunPod serverless ($0.20–$0.50/hour).
  - *Pros:* Inference throughput increases from 5 FPS to 35+ FPS.
  - *Cons:* High monthly idle cost ($50–$150/month); unnecessary for portfolio demonstration. **Not recommended.**

---

## 5. Cloud Hosting Provider Comparison

| Provider | Tier / Plan | vCPU / RAM | Monthly Cost | Cold Start Behavior | Persistent Storage | Verdict for CargoVision AI |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Hugging Face Spaces** | CPU Basic (Free) | 2 vCPU / **16 GB RAM** | **$0.00 (Free)** | Sleeps after 48h; wakes on HTTP request (~30s) | Ephemeral or mounted Dataset repo | **Primary Recommendation:** 16 GB RAM eliminates OOM crashes; zero hosting cost. |
| **Render** | Free Tier | 0.1 vCPU / **512 MB RAM** | $0.00 (Free) | Sleeps after 15m; wakes in ~50s | Ephemeral | **Incompatible:** 512 MB RAM ceiling triggers OOM SIGKILL during model loading. |
| **Render** | Starter (Paid) | 1 vCPU / **1.0 GB RAM** | $7.00 (~₹585) | Always-on (no sleep) | $0.25/GB/mo persistent disk | **Viable Fallback:** 1 GB RAM supports 744 MB peak, but tight margin under concurrent load. |
| **Railway** | Hobby / Usage | Dynamic (up to 8 GB) | ~$5.00 (~₹415) | Sleep on idle or always-on | Persistent volume supported ($0.50/GB) | **Viable:** Good developer experience, flexible memory allocation. |
| **Fly.io** | `shared-cpu-1x` (1 GB) | 1 vCPU / 1.0 GB RAM | $3.19 (~₹265) | Auto-stop / auto-start | 3 GB free persistent volume | **Viable Budget Option:** Low cost, supports volume mounts for SQLite. |
| **Cloudflare Pages** | Free (Frontend) | Unlimited CDN | **$0.00 (Free)** | Instant (0s) | N/A (Static) | **Best-in-Class for Frontend.** |

---

## 6. Security & Abuse Prevention Audit

Deploying a public endpoint accepting video uploads introduces denial-of-service and storage exhaustion risks:

1. **Unbounded Memory Uploads:**
   - *Current Code:* `await file.read()` loads entire upload into RAM at once.
   - *Fix:* Enforce chunked streaming to temporary disk files with a strict `MAX_UPLOAD_SIZE_MB = 30` limit.
2. **File Type & Extension Spoofing:**
   - *Fix:* Validate file extension against `ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}` and inspect video container magic bytes via OpenCV header parsing before queuing.
3. **Concurrent Job Exhaustion:**
   - *Risk:* Multiple simultaneous video processing tasks on CPU will exhaust container memory.
   - *Fix:* Introduce a concurrency semaphore (`MAX_CONCURRENT_JOBS = 1`). Return `429 Too Many Requests` if an inspection is already actively processing.
4. **Filename Sanitization:**
   - *Fix:* Use `uuid.uuid4()` prefixed safe filenames; prevent directory traversal (`../../`).
5. **CORS Hardening:**
   - *Fix:* Replace wildcard `["*"]` with an environment-configured whitelist (`CORS_ORIGINS`).

---

## 7. Recommended Roadmap & Next Steps

1. **Phase 3–8 Implementation (Code Preparation):**
   - Centralize frontend API base URL (`VITE_API_BASE_URL`) across all components.
   - Configure environment-driven CORS, storage directories, and database paths.
   - Implement upload file-size validation, chunked streaming, and concurrency locking.
   - Create production-ready `Dockerfile`, `.dockerignore`, and deployment documentation.
2. **Phase 10 (Verification):**
   - Run local regression test suite and production build.
3. **Phase 12 (User Approval Gate):**
   - Present final deployment audit and await user instruction before provisioning external services.
