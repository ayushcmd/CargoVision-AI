# CargoVision AI — Intelligent Railway Wagon Inspection

<div align="center">

![CargoVision AI Logo](frontend/public/PhotoshopExtension_Image%20(1).png)

**Automated Railway Wagon Inspection & Defect Analysis with Computer Vision & Deep Learning**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/React-19.2-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.156-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Features](#-key-features) • [Architecture](#-architecture) • [Installation & Setup](#-installation--setup) • [Local URLs](#-local-urls) • [API Reference](#-api-endpoints) • [Troubleshooting](#-troubleshooting) • [Attribution & Licenses](#-attribution--licenses)

</div>

---

## 🎯 System Overview

**CargoVision AI** is an advanced, automated vision inspection and telemetry system designed for railway freight wagon monitoring. Built on deep learning and high-throughput computer vision, the platform processes high-speed trackside video streams, camera feeds, and video uploads to detect wagons, recognize standard 11-digit Indian Railways identification markings, enhance nighttime imagery, flag structural damage, and generate comprehensive compliance reports.

### Primary Capabilities

- **Automated Wagon Detection & Tracking**: Real-time identification and continuous tracking of rolling stock wagons.
- **OCR Wagon Number Recognition**: Automatic detection, cropping, and parsing of standard 11-digit Indian Railways wagon numbers with checksum verification.
- **Low-Light & Night-Time Enhancement**: Integrated Zero-DCE and deep enhancement models for clear visibility during evening and tunnel transits.
- **Structural Defect & Anomaly Detection**: Classification and localized bounding of anomalies (spring damage, door defects, axle faults, structural deformations).
- **Executive PDF Reporting**: Automatic generation of industry-standard inspection reports including timestamps, detected wagon IDs, condition status, and visual captures.
- **Real-Time Analytics Dashboard**: Live metrics covering wagon volume, defect ratios, processing FPS, and historical audit logs.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Frontend (React 19 + Vite)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Live Feed UI │  │ Video Upload │  │ History & Report │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             ↕ HTTP / REST & Stream Feeds
┌─────────────────────────────────────────────────────────────┐
│                 Backend (FastAPI + Python)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ REST APIs    │  │ Video Engine │  │ PDF Report Gen   │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             ↕
┌─────────────────────────────────────────────────────────────┐
│                 Cascaded AI Vision Pipeline                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ YOLOv8 Wagon │→ │ YOLOv8 Num   │→ │ EasyOCR Text     │   │
│  │ Detector (A) │  │ Detector (B) │  │ Recognition      │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│         │                 │                   │             │
│         ▼                 ▼                   ▼             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ YOLOv8 Damage│  │ NAFNet/      │  │ SQLite DB        │   │
│  │ Detector (C) │  │ Zero-DCE     │  │ Storage & Cache  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Technology Stack

### Backend
- **Framework**: FastAPI with Uvicorn ASGI server
- **Computer Vision**: OpenCV, Ultralytics YOLOv8, PyTorch, Torchvision
- **OCR Engine**: EasyOCR with custom Indian Railways 11-digit parser
- **Image Enhancement**: Zero-DCE & NAFNet architecture
- **Reporting & Storage**: FPDF2, SQLite3
- **Streaming**: Multipart MJPEG streaming and background task queues

### Frontend
- **Framework**: React 19 with Vite 7
- **Styling**: Tailwind CSS 4
- **Visualizations**: Recharts
- **Icons**: Lucide React
- **Routing**: React Router DOM 7

---

## ⚙️ Windows Prerequisites

- **Operating System**: Windows 10 / 11 (64-bit)
- **Python**: Python 3.11 (Recommended; 3.12 compatible)
- **Node.js**: v18.0.0 or higher (v24 tested)
- **Git**: 2.40+
- **Hardware**: 8 GB RAM minimum (16 GB recommended), CUDA-enabled GPU (optional; CPU inference is fully supported with automatic fallbacks)

---

## 🚀 Installation & Setup

### 1. Backend Setup

From the repository root:

```powershell
# 1. Create a Python 3.11 virtual environment
py -3.11 -m venv .venv

# 2. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install backend requirements
pip install --upgrade pip
pip install fastapi uvicorn python-multipart pydantic numpy opencv-python Pillow torch torchvision ultralytics easyocr fpdf2 yt-dlp requests lapx

# 4. Optional: Configure environment variables
Copy-Item .env.example .env

# 5. Start the FastAPI server
cd "full model/src/api"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup

In a new terminal:

```powershell
# 1. Navigate to frontend directory
cd "C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI\frontend"

# 2. Install dependencies (respecting lockfile)
npm install

# 3. Start development server
npm run dev -- --host 127.0.0.1 --port 5173
```

---

## 🌐 Local URLs

| Component | URL | Notes |
|-----------|-----|-------|
| **Frontend Application** | [http://127.0.0.1:5173](http://127.0.0.1:5173) | Main user interface |
| **Backend API Root** | [http://127.0.0.1:8000](http://127.0.0.1:8000) | Root service endpoint |
| **API Health Check** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Service health check |
| **Swagger Interactive Docs** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive API testing |
| **Redoc API Documentation** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | Alternative API specification |

---

## 🤖 Model Weights & Datasets

Pre-trained weights are located locally inside the project structure:

- **Wagon Detection**: `full model/railway_hackathon_take6/merged_model_v6_generalized/weights/best.pt`
- **Number Plate Detection**: `full model/railway_hackathon_numbers/number_detector_v1/weights/best.pt`
- **Damage Detection**: `full model/railway_hackathon_damage/damage_detector_v1/weights/best.pt`
- **Zero-DCE Enhancement**: `full model/zero_dce_model/Epoch99.pth`
- **NAFNet Enhancement**: `full model/NAFnet/NAFNet-GoPro-width32.pth`
- **Wagon Number OCR Models**: `wagon number detection/wnd/models/wagonNumberDetectionV2.pt`

> [!NOTE]
> CargoVision AI features smart path resolution in `main.py` that automatically maps available trained weights to the inference pipeline without requiring manual retraining.

---

## 📊 API Endpoints

```http
GET  /health                          # Health check endpoint
GET  /history                         # List all past wagon inspections
GET  /history/{id}                    # Get detailed detections and crops for an inspection
GET  /history/{id}/report             # Download PDF report for inspection run
POST /upload                          # Upload video file to trigger automatic inspection
GET  /inspections/{id}/status         # Query pipeline status (PROCESSING / COMPLETED)
GET  /stream/processing/{id}          # MJPEG preview stream of live pipeline inference
GET  /stats                           # Real-time statistics summary
GET  /api/analytics                   # Aggregated metrics for analytics graphs
POST /live/start?stream_id={id}       # Attach pipeline to live RTSP/YouTube stream
POST /live/stop                       # Disconnect pipeline from live stream
POST /api/search                      # Natural language AI database search (requires GROQ_API_KEY)
```

---

## 🔧 Troubleshooting

- **`WinError 5 Access Denied` on `lap` installation**:
  Use `pip install lapx` instead of `lap`. `lapx` includes pre-built Windows wheels that do not require MSVC compilation.
- **Port Conflict**:
  If port 8000 or 5173 is occupied, specify custom ports using `--port <number>` on either Uvicorn or Vite.
- **First-time OCR Download Delay**:
  On first invocation, EasyOCR downloads the text detection (`craft`) and character recognition models (~40MB) into `~/.EasyOCR`. Subsequent runs load instantaneously from cache.
- **CUDA Out of Memory**:
  If running on a low-VRAM GPU (≤4 GB), the pipeline automatically cascades and supports CPU execution seamlessly.

---

## 🌐 Public Demo & Deployment

CargoVision AI is configured for production deployment on containerized cloud platforms. Comprehensive architectural analyses, resource measurements, and setup guides are provided:

- **[Hosting Feasibility Audit](deployment/DEPLOYMENT_AUDIT.md)**: Empirical RAM/CPU measurements, model footprints, provider pricing comparisons (Hugging Face Spaces, Render, Railway, Fly.io), and resource budgets.
- **[Deployment & Operations Guide](deployment/DEPLOYMENT_GUIDE.md)**: Step-by-step procedures for zero-cost deployment on Hugging Face Spaces + Cloudflare Pages, Docker containerization, environment variables, and security policies.

---

## 📜 Attribution & Licenses

This project is an independently maintained and enhanced implementation based on the open-source **GARUD** railway wagon inspection project originally developed by **P47Parzival**:

- **Upstream Repository**: [https://github.com/P47Parzival/low-light-image-deblur.git](https://github.com/P47Parzival/low-light-image-deblur.git)
- **Original License**: MIT License (retained in respective component trees)
- **Third-Party Model Licenses**:
  - Ultralytics YOLOv8: AGPL-3.0 License
  - EasyOCR: Apache-2.0 License
  - FastAPI: MIT License
  - React & Vite: MIT License
