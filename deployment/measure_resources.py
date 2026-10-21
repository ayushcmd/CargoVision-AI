import os
import sys
import time
import json
import psutil
import cv2
import numpy as np

# Ensure root is in sys.path
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('full model'))
sys.path.append(os.path.abspath('full model/src/core'))

process = psutil.Process(os.getpid())

def get_ram_mb():
    return process.memory_info().rss / (1024 * 1024)

def measure():
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platform": sys.platform,
        "stages": {}
    }

    m0 = get_ram_mb()
    print(f"[STAGE 0] Initial Process RSS: {m0:.2f} MB")
    report["stages"]["baseline_process_mb"] = round(m0, 2)

    # 1. Imports
    t0 = time.time()
    import torch
    from ultralytics import YOLO
    import easyocr
    from deblur_engine import DeblurGANEngine
    from ocr_engine import WagonOCR
    dt_imports = (time.time() - t0) * 1000
    m_imports = get_ram_mb()
    print(f"[STAGE 1] Post-Imports RSS: {m_imports:.2f} MB (+{m_imports - m0:.2f} MB) in {dt_imports:.1f} ms")
    report["stages"]["post_imports"] = {
        "rss_mb": round(m_imports, 2),
        "delta_mb": round(m_imports - m0, 2),
        "time_ms": round(dt_imports, 1)
    }

    # 2. Model Loading
    t0 = time.time()
    print("[STAGE 2] Loading YOLO Models & Engines...")
    m_a = YOLO("full model/railway_hackathon_take6/merged_model_v6_generalized/weights/best.pt")
    m_b = YOLO("wagon number detection/wnd/models/WNDEModelV2.pt")
    m_c = YOLO("full model/railway_hackathon_damage/damage_detector_v1/weights/best.pt")
    deblur = DeblurGANEngine("full model/NAFnet/NAFNet-GoPro-width32.pth")
    ocr = WagonOCR()

    dt_load = (time.time() - t0) * 1000
    m_models = get_ram_mb()
    print(f"[STAGE 2] All Models Loaded RSS: {m_models:.2f} MB (+{m_models - m_imports:.2f} MB) in {dt_load:.1f} ms")
    report["stages"]["models_loaded"] = {
        "rss_mb": round(m_models, 2),
        "delta_mb": round(m_models - m_imports, 2),
        "load_time_ms": round(dt_load, 1)
    }

    # 3. Image Inference
    sample_img_path = "evaluation/data/frames/number_frame_30.jpg"
    img = cv2.imread(sample_img_path)
    h, w = img.shape[:2]

    t0 = time.time()
    res_a = m_a.predict(img, conf=0.25, imgsz=640, verbose=False)[0]
    dt_a = (time.time() - t0) * 1000

    t_ocr_total = 0.0
    wagon_crops = 0
    for b in res_a.boxes:
        bx = list(map(int, b.xyxy[0].tolist()))
        crop = img[max(0, bx[1]):min(h, bx[3]), max(0, bx[0]):min(w, bx[2])]
        if crop.size > 0:
            wagon_crops += 1
            # Run Model B
            res_b = m_b.predict(crop, conf=0.3, imgsz=640, verbose=False)[0]
            for nb in res_b.boxes:
                nbx = list(map(int, nb.xyxy[0].tolist()))
                ncrop = crop[max(0, nbx[1]):min(crop.shape[0], nbx[3]), max(0, nbx[0]):min(crop.shape[1], nbx[2])]
                if ncrop.size > 0:
                    t_ocr0 = time.time()
                    txt = ocr.process_wagon(ncrop)
                    t_ocr_total += (time.time() - t_ocr0) * 1000

    m_image_inf = get_ram_mb()
    print(f"[STAGE 3] Image Inference Peak RSS: {m_image_inf:.2f} MB (Model A: {dt_a:.1f} ms, OCR Total: {t_ocr_total:.1f} ms)")
    report["stages"]["single_image_inference"] = {
        "rss_mb": round(m_image_inf, 2),
        "model_a_latency_ms": round(dt_a, 1),
        "ocr_latency_ms": round(t_ocr_total, 1),
        "wagon_boxes": len(res_a.boxes)
    }

    # 4. Video Inference (30 frames)
    video_path = "Assests/wagon_number_detection2.mp4"
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_in = cap.get(cv2.CAP_PROP_FPS) or 30

    frames_to_process = min(30, total_frames)
    t0_video = time.time()
    processed_count = 0
    max_ram_during_video = m_image_inf

    for i in range(frames_to_process):
        ret, frame = cap.read()
        if not ret:
            break
        processed_count += 1
        # Model A
        res = m_a.predict(frame, conf=0.25, imgsz=640, verbose=False)[0]
        cur_ram = get_ram_mb()
        if cur_ram > max_ram_during_video:
            max_ram_during_video = cur_ram

    cap.release()
    total_video_time = time.time() - t0_video
    throughput_fps = processed_count / total_video_time if total_video_time > 0 else 0.0

    print(f"[STAGE 4] Video Inference (30 frames): {total_video_time:.2f}s ({throughput_fps:.2f} FPS), Peak RSS: {max_ram_during_video:.2f} MB")
    report["stages"]["video_inference_30_frames"] = {
        "frames_processed": processed_count,
        "duration_sec": round(total_video_time, 2),
        "throughput_fps": round(throughput_fps, 2),
        "peak_rss_mb": round(max_ram_during_video, 2)
    }

    with open("deployment/measured_resources.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\nSaved measured resources to deployment/measured_resources.json")

if __name__ == "__main__":
    measure()
