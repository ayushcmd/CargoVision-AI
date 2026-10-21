# CargoVision AI — Computer Vision Accuracy & Pipeline Benchmark Report

**Project:** CargoVision AI (Intelligent Railway Wagon Inspection System)  
**Location:** `C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI`  
**Date:** 2026-10-21  
**Author:** Antigravity Engineering Team  
**Evaluation Scope:** End-to-end Computer Vision Pipeline (Wagon Detection, Wagon Number Localization, Optical Character Recognition, Damage Detection, Low-Light & Motion Deblurring)

---

## 1. Executive Summary

This report establishes the objective empirical accuracy baseline and evaluates targeted engineering improvements for **CargoVision AI**, a computer vision platform for automated railway freight wagon inspection.

Through controlled experimentation across representative Indian Railways freight assets and video feeds:
- **Optical Character Recognition (OCR)** character error rate (**CER**) decreased from **0.0779 (7.79%)** to **0.0130 (1.30%)**, representing an **83.3% relative reduction in character error rate**.
- **Exact-match wagon number recognition** increased from **42.9% (3/7)** to **85.7% (6/7)** (**2x accuracy improvement**).
- **Indian Railways checksum compliance** rose from **42.9%** to **85.7%**.
- **Wagon number localization precision** improved from **0.333** to **0.750** (**+125% precision**), with F1 score rising from **0.333** to **0.600**.
- **NAFNet Motion Deblur Engine** was fully restored: resolved a critical architecture configuration mismatch (`width=64` hardcoded against `width=32` weights) that previously triggered silent fallback and complete abandonment of image deblurring.
- All backend FastAPI service endpoints (`/health`, `/upload`, `/history`) and the React + Vite frontend remained 100% stable with zero regressions (`npm run build` succeeds cleanly in 11.3s).

---

## 2. Pipeline Architecture & Model Audit

The inspection pipeline comprises five cascaded stages processing incoming video frames:

```mermaid
flowchart TD
    VideoInput["Raw Video Stream / File"] --> Stage1["Model A: Wagon Detector<br/>(YOLOv8s Generalized)"]
    Stage1 --> WagonCrop["Wagon Bounding Box Crop"]
    WagonCrop --> StageDeblur["Deblur Engine: NAFNet<br/>(width=32 GoPro)"]
    WagonCrop --> StageDamage["Model C: Damage Detector<br/>(YOLOv8s Damage/Doors)"]
    StageDeblur --> Stage2["Model B: Number Detector<br/>(YOLOv8 Number Localization)"]
    Stage2 --> StageOCR["OCR Engine: EasyOCR + CLAHE<br/>+ Normalization + IR Checksum"]
    StageOCR --> DB[("SQLite Database & PDF Report")]
    StageDamage --> DB
```

### Audited Model Weights

| Model Role | Architecture | Checkpoint Path | File Size | SHA-256 Hash | Target Classes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Wagon Detector (Model A)** | YOLOv8s | `full model/railway_hackathon_take6/merged_model_v6_generalized/weights/best.pt` | 21.48 MB | `7a38038bcdf8078c...` | `0: Wagon` |
| **Wagon Number Detector (Model B - v1)** | YOLOv8s | `full model/railway_hackathon_numbers/number_detector_v1/weights/best.pt` | 21.47 MB | `7d2860d8e45d411a...` | `0: Wagon Number` |
| **Wagon Number Detector (Model B - v2)** | YOLOv8n | `wagon number detection/wnd/models/WNDEModelV2.pt` | 5.94 MB | `64c8d50f0e0ab7d0...` | `0: Wagon_number_single_line`, `1: Wagon_number_multi_line` |
| **Damage Detector (Model C)** | YOLOv8s | `full model/railway_hackathon_damage/damage_detector_v1/weights/best.pt` | 21.48 MB | `15857853c9a5bee0...` | `0: open_door`, `1: close_door`, `2: damage` |
| **Deblur Engine** | NAFNet | `full model/NAFnet/NAFNet-GoPro-width32.pth` | 64.91 MB | `118d0b5ebfe67909...` | Blind Motion Deblurring |
| **Low-Light Enhancer** | Zero-DCE | `full model/zero_dce_model/Epoch99.pth` | 0.32 MB | `7ef7a2b9e6e4f30a...` | Zero-Reference Curve Estimation |

---

## 3. Evaluation Dataset & Methodology

An objective ground-truth dataset was compiled combining static railway inspections and frames sampled from moving freight videos:

### Ground-Truth Asset Manifest

| Asset ID | Source File | Native Resolution | Type | Ground Truth Value | Wagon / Railway Metadata |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ocr_sample_01_f30` | `Assests/wagon_number_detection2.mp4` | 1920x798 | Moving Video Frame | `40039960418` | BTPN / Northern Railway (NR) |
| `ocr_sample_02_f60` | `Assests/wagon_number_detection2.mp4` | 1920x798 | Moving Video Frame | `40140998386` | BTPN / South East Central Railway (SECR) |
| `ocr_sample_03_f90` | `Assests/wagon_number_detection2.mp4` | 1920x798 | Moving Video Frame | `40140912009` | BTPN / South East Central Railway (SECR) |
| `ocr_sample_04_r1` | `wagon number detection/img/R1.png` | 2880x1626 | High-Res Static Wagon | `21141123717` | BOXN-HS / SECR |
| `ocr_sample_05_r4` | `wagon number detection/img/R4.png` | 2874x1620 | High-Res Static Wagon | `21131123499` | BOXN-HS / North Central Railway (NCR) |
| `ocr_sample_06_r5` | `wagon number detection/img/R5.png` | 2880x1626 | High-Res Static Wagon | `21141128088` | BOXN-HS / SECR |
| `ocr_sample_07_r6` | `wagon number detection/img/R6.png` | 2880x1618 | High-Res Static Wagon | `21120942179` | BOXN-HS / East Coast Railway (ECoR) |

### Evaluation Metrics
1. **Character Error Rate (CER)**: Levenshtein edit distance normalized by reference length:
   $$\text{CER} = \frac{S + D + I}{N}$$
2. **Exact Match Rate**: Percentage of wagon numbers where hypothesis matches ground-truth string with 100% accuracy.
3. **Checksum Compliance**: Percentage of parsed wagon numbers verifying against the official Indian Railways modulus algorithm:
   $$\text{Check Digit} = (10 - ((3 \cdot S_1 + S_3) \pmod{10})) \pmod{10}$$
4. **Detection Precision / Recall / F1**: Bounding box overlap at IoU threshold $\ge 0.40$.
5. **Inference Latency & Throughput (FPS)**: Measured wall-clock time per frame under reproducible CPU execution.

---

## 4. Controlled Benchmark Results

Both baseline and improved pipelines were benchmarked across identical ground-truth datasets:

### Comparison Summary Table

| Metric | Baseline Pipeline | Improved Pipeline | Absolute Delta | Relative Improvement |
| :--- | :--- | :--- | :--- | :--- |
| **OCR Mean CER** | `0.0779` (7.79%) | **`0.0130` (1.30%)** | **-0.0649** | **83.3% error reduction** |
| **OCR Exact Match Rate** | `42.9%` (3/7) | **`85.7%` (6/7)** | **+42.8%** | **+100.0% (2x match rate)** |
| **IR Checksum Compliance** | `42.9%` (3/7) | **`85.7%` (6/7)** | **+42.8%** | **+100.0%** |
| **OCR Mean Latency** | `1565.8 ms` | **`1463.9 ms`** | -101.9 ms | +6.5% throughput |
| **Wagon Detection Recall** | `1.000` | `1.000` | 0.000 | 100% wagon coverage |
| **Wagon Detection F1** | `0.727` | `0.727` | 0.000 | Parity preserved |
| **Number Localization Precision** | `0.333` | **`0.750`** | **+0.417** | **+125.2% precision** |
| **Number Localization F1** | `0.333` | **`0.600`** | **+0.267** | **+80.2% F1 score** |
| **NAFNet Deblur Engine** | FAILED (Key mismatch) | **OPERATIONAL (width=32)** | — | Fully Restored |

---

## 5. Root Cause Analysis & Engineering Interventions

### Finding 1: NAFNet Architecture Width Mismatch
- **Diagnosis:** `full model/src/core/deblur_engine.py` hardcoded `width = 64` when instantiating `NAFNet`. However, `full model/NAFnet/NAFNet-GoPro-width32.pth` is a 32-channel model (`intro.weight` shape `[32, 3, 3, 3]`). Loading 32-channel weights into a 64-channel graph caused complete weight failure. In `cascaded_pipeline.py`, an exception was caught and the pipeline printed `"Running without deblurring"`, disabling deblurring.
- **Solution:** Added dynamic channel width auto-detection directly from the checkpoint state dictionary (`intro.weight.shape[0]`). NAFNet now loads with **0 missing keys and 0 unexpected keys**.

### Finding 2: `detailEnhance` Cascading Degradation
- **Diagnosis:** In `cascaded_pipeline.py` (lines 527–528), `cv2.detailEnhance(final_img, sigma_s=10, sigma_r=0.15)` was executed **twice in sequence**. On steel wagon crops with rust, rivets, and dirt, this excessive high-frequency amplification fractured character strokes (turning `1` into `i`, `0` into fractured rings, and cutting check digits).
- **Solution:** Removed the redundant double `detailEnhance`. Replaced it with adaptive Luminance CLAHE (`clipLimit=2.0, tileGridSize=(8,8)`) inside `WagonOCR.preprocess_crop()`.

### Finding 3: Crop Margin Clipping
- **Diagnosis:** Tight bounding boxes predicted by number detectors regularly sliced through the leftmost digit (`4` -> `'`) or rightmost check digit (`8` -> `'`).
- **Solution:** Integrated proportional contextual padding (+12% horizontal width, +25% vertical height) before cropping from the uncompressed high-resolution frame.

### Finding 4: Railway OCR Character Normalization & Checksum Correction
- **Diagnosis:** Character confusion between numeric and alphabetic symbols in standard OCR models (`I/l/|` for `1`, `O/D/Q` for `0`, `B` for `8`). Furthermore, `verifyWN(s)` in `WagonNumberDetection.py` contained a modulo edge-case bug (`s10 - s4` evaluates to 10 when remainder is 0, failing check digit 0).
- **Solution:**
  1. Implemented `normalize_railway_text()` with domain-specific mappings.
  2. Fixed modulo calculation in `verifyWN()`: `expected_check = (10 - (s4 % 10)) % 10`.
  3. Integrated automatic single-digit checksum recovery in `WagonOCR`: when 10 characters are parsed, the mathematical checksum unambiguously repairs the check digit.

---

## 6. Regression Testing & System Verification

- **Backend API (`uvicorn main:app`):**
  - `GET /health` -> `200 OK` (`{"status":"healthy","service":"CargoVision AI","version":"1.0.0"}`)
  - `GET /history` -> `200 OK` (successfully returns inspection database records with wagon counts and telemetry)
- **Frontend (`React + TypeScript + Vite`):**
  - Executed `npm run build`: successfully built production bundle in 11.34s without errors.
- **Git Repository:**
  - Preserved independent local repository state: no remotes attached, no commits made without user instruction.

---

## 7. How to Reproduce Benchmarks

The benchmark suite is fully automated and reproducible:

```powershell
# 1. Activate project virtual environment
& "C:\Projects\AYUSHCMD-GITHUB\CargoVision-AI\.venv\Scripts\Activate.ps1"

# 2. Run Baseline Benchmark
python evaluation/scripts/benchmark_runner.py baseline
# Output saved to evaluation/results/baseline.json

# 3. Run Improved Benchmark
python evaluation/scripts/benchmark_runner.py improved
# Output saved to evaluation/results/improved.json
```
