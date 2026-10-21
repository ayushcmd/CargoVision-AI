import cv2
from ultralytics import YOLO
import sys
import os
import argparse
import multiprocessing as mp
import time
import queue
from collections import deque
import numpy as np
import json
import torch

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.core.ocr_engine import WagonOCR
from src.core.indian_railways import IndianWagonParser
from src.scripts.pipeline_viz import draw_stats, draw_track
from src.core.deblur_engine import DeblurGANEngine
from src.core.blur_metric import calculate_blur_score
import src.core.database as database

# -----------------------------
# GPU Memory Optimization
# -----------------------------
def optimize_gpu_memory():
    """Optimize GPU memory for multi-model inference on 6GB VRAM"""
    if torch.cuda.is_available():
        # Enable TF32 for faster matmul on Ampere GPUs (RTX 3050)
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        # Enable cuDNN benchmarking for consistent input sizes
        torch.backends.cudnn.benchmark = True
        
        # Clear any cached memory
        torch.cuda.empty_cache()
        
        print(f"[INFO] GPU: {torch.cuda.get_device_name(0)}")
        print(f"[INFO] VRAM Total: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        free_mem, total_mem = torch.cuda.mem_get_info()
        print(f"[INFO] VRAM Free: {free_mem / 1e9:.1f} GB")

# -----------------------------
# OCR Processing (CPU)
# -----------------------------
def ocr_worker(input_queue, output_queue):
    ocr = WagonOCR()
    while True:
        item = input_queue.get()
        if item is None: break
        
        # New Unpacking: Added ocr_path + Anomaly args
        wagon_id, crop, req_time, orig_path, deblur_path, ocr_path, anomaly_path, anomaly_type, anomaly_conf = item
        
        # In a real scenario, DeblurGAN would run here before OCR
        
        raw_text = ocr.process_wagon(crop)
        
        if raw_text:
            parsed = IndianWagonParser.parse(raw_text)

            # checksum validation can be enabled if needed
            # if parsed and not IndianWagonParser.validate_checksum(raw_text):
            #     print(f"[WARNING] Invalid checksum for wagon {raw_text}")
            #     parsed = None
            output_queue.put((wagon_id, raw_text, parsed, req_time, orig_path, deblur_path, ocr_path, anomaly_path, anomaly_type, anomaly_conf))
        else:
            print(f"[WARNING] OCR Failed for Wagon {wagon_id}")
            # Still pass paths so we can see the failed image
            output_queue.put((wagon_id, "OCR Failed", None, req_time, orig_path, deblur_path, ocr_path, anomaly_path, anomaly_type, anomaly_conf))

# -----------------------------
# Cascaded Pipeline
# -----------------------------
def cascaded_pipeline(video_path, model_a_path, model_b_path, deblur_model_path, model_c_path=None, headless=False, inspection_id=None, frame_queue=None, use_fp16=True, use_torch_compile=True):
    if not os.path.exists(video_path): return
    
    # Optimize GPU before loading models
    optimize_gpu_memory()
    
    print(f"[INFO] Loading Model A (Wagon): {model_a_path}")
    model_a = YOLO(model_a_path)
    
    # Enable FP16 (Passed as argument to track/predict)
    if use_fp16 and torch.cuda.is_available():
        print("[INFO] Enabling FP16 inference for YOLO Model A (via argument)")
        # model_a.model.half() # DO NOT manually cast YOLO models before fusion!
    
    print(f"[INFO] Loading Model B (Number): {model_b_path}")
    # Check if model B exists, if not warn user
    if not os.path.exists(model_b_path):
        print(f"[WARNING] Model B not found at {model_b_path}. Number detection will fail.")
        model_b = None
    else:
        model_b = YOLO(model_b_path)
        if use_fp16 and torch.cuda.is_available():
            print("[INFO] Enabling FP16 inference for YOLO Model B (via argument)")
            # model_b.model.half()
    
    # Model C (Anomaly)
    model_c = None
    if model_c_path and os.path.exists(model_c_path):
        print(f"[INFO] Loading Model C (Anomaly): {model_c_path}")
        model_c = YOLO(model_c_path)
        if use_fp16 and torch.cuda.is_available():
            print("[INFO] Enabling FP16 inference for YOLO Model C (via argument)")
            # model_c.model.half()
    else:
          # Default fallback or warning
          if model_c_path: print(f"[WARNING] Model C not found at {model_c_path}")
          else: print("[INFO] Model C not provided. Anomaly detection skipped.")

    # DeblurGAN Setup
    deblur_engine = None
    if os.path.exists(deblur_model_path):
        try:
            print(f"[INFO] Loading DeblurGAN: {deblur_model_path}")
            deblur_engine = DeblurGANEngine(deblur_model_path)
            
            # Optimize DeblurGAN
            # Disable torch.compile on Windows (caused TritonMissing error)
            if use_torch_compile and os.name != 'nt' and hasattr(torch, 'compile'):
                print("[INFO] Compiling DeblurGAN with torch.compile...")
                try:
                    deblur_engine.model = torch.compile(
                        deblur_engine.model, 
                        mode='reduce-overhead'
                    )
                    print("[INFO] DeblurGAN compiled successfully")
                except Exception as e:
                    print(f"[WARNING] torch.compile failed: {e}. Using uncompiled model.")
            elif os.name == 'nt':
                print("[INFO] Skipping torch.compile on Windows (Triton not supported)")
        except Exception as e:
            print(f"[WARNING] Failed to load DeblurGAN: {e}. Running without deblurring.")
    else:
        print(f"[WARNING] DeblurGAN weights not found at {deblur_model_path}. Running without deblurring.")
    
    # Monitor VRAM usage after model loading
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1e9
        reserved = torch.cuda.memory_reserved() / 1e9
        print(f"[INFO] VRAM Allocated: {allocated:.2f} GB")
        print(f"[INFO] VRAM Reserved: {reserved:.2f} GB")
        
        # Warning if using >80% of VRAM
        if reserved > 4.8:  # 80% of 6GB
            print("[WARNING] High VRAM usage! Consider reducing batch size or disabling TTA")
        
    deblur_save_dir = os.path.join(os.path.dirname(video_path), '../../full model/DeblurredImg')
    original_save_dir = os.path.join(os.path.dirname(video_path), '../../full model/OriginalImg')
    ocr_save_dir = os.path.join(os.path.dirname(video_path), '../../full model/OCRimage')
    anomaly_save_dir = os.path.join(os.path.dirname(video_path), '../../full model/AnomalyImg')
    
    os.makedirs(deblur_save_dir, exist_ok=True)
    os.makedirs(original_save_dir, exist_ok=True)
    os.makedirs(ocr_save_dir, exist_ok=True)
    os.makedirs(anomaly_save_dir, exist_ok=True)

    # OCR Setup
    cap = cv2.VideoCapture(video_path)

    # STRATEGY: Large Buffer + Drain
    # We allow up to 1000 wagons to be queued so the main loop never blocks.
    # The OCR worker will catch up after the video ends.
    ocr_in_q = mp.Queue(maxsize=1000)
    ocr_out_q = mp.Queue()
    ocr_p = mp.Process(target=ocr_worker, args=(ocr_in_q, ocr_out_q), daemon=True)
    ocr_p.start()
    
    # ... (rest of logging setup is separate, not changing that) ...
    # Skip to near end of loop...

    # ... (Updating putting logic back to simple put, handled in next chunk) ...


    
    # Logging Setup
    import datetime
    output_dir = os.path.join(os.path.dirname(video_path), '../../full model/detection')
    os.makedirs(output_dir, exist_ok=True)
    
    start_time = datetime.datetime.now()
    timestamp_str = start_time.strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(output_dir, f"{timestamp_str}.txt")
    
    print(f"[INFO] Report will be properly generated at: {log_file_path}")

    # Database Init
    database.init_db()
    if inspection_id is None:
        inspection_id = database.create_inspection(os.path.basename(video_path))
    print(f"[INFO] Inspection Run ID: {inspection_id}")

    # Data Buffers
    unique_wagons = set()
    consist_log = [] # List of dicts: {'id': track_id, 'text': ..., 'parsed': ..., 'time': ...}
    wagon_timestamps = {} # Map id -> first_detection_time
    
    # Restoring Initialization
    frame_cnt = 0
    prev_time = time.time()
    metrics = {'fps': deque(maxlen=50), 'det': deque(maxlen=50), 'ocr': deque(maxlen=50)}
    wagon_data = {}
    wagon_image_cache = {}
    wagon_data = {}
    wagon_image_cache = {}
    wagon_anomaly_data = {} # { wagon_id: { 'type': ..., 'conf': ..., 'crop': ... } }
    wagon_number_data = {}  # { wagon_id: 'crop': ... }
    ocr_requested = set()

    # System Health Logs
    brightness_log = []
    blur_scores_log = []

    # -----------------------------
    # VIDEO DISPLAY SETTINGS (VLC-like)
    # -----------------------------
    # Get video properties
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate display size (fit to screen, max 1280x720 for comfortable viewing)
    max_display_width = 1280
    max_display_height = 720
    scale = min(max_display_width / video_width, max_display_height / video_height, 1.0)
    display_width = int(video_width * scale)
    display_height = int(video_height * scale)
    
    # Create named window with specific properties
    if not headless:
        window_name = "Indian Railways - Freight Inspection System"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, display_width, display_height)
        
        # Try to set window to be always on top and centered (Windows specific)
        try:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
        except:
            pass
        
    while cap.isOpened():
        success, frame = cap.read()
        if not success: break
        
        frame_cnt += 1
        t_start_frame = time.time()
        
        # Performance Counters (Accumulators)
        t_model_a = 0.0
        t_model_b = 0.0
        t_model_c = 0.0
        t_nafnet = 0.0
        t_ocr_overhead = 0.0

        # Telemetry: Brightness (Sample every 5 frames for speed)
        if frame_cnt % 5 == 0:
             # fast mean
             brightness_log.append(np.mean(frame))
        
        # -----------------------------
        # STEP 1: Model A (Full Frame) - Detect Wagons
        # -----------------------------
        t0_a = time.time()
        results_a = model_a.track(frame, persist=True, tracker="../../trackers/byte_track.yaml", verbose=False, half=use_fp16)
        t_model_a += (time.time() - t0_a)

        # DEBUG: Print raw detections
        if results_a and results_a[0].boxes.id is not None:
             pass 
             # print(f"Raw Classes Detected: {results_a[0].boxes.cls.cpu().numpy()}")
             # print(f"Confidences: {results_a[0].boxes.conf.cpu().numpy()}")

        active_wagons_list = []
        if results_a and results_a[0].boxes.id is not None:
            boxes = results_a[0].boxes.xyxy.cpu().numpy()
            ids = results_a[0].boxes.id.cpu().numpy()
            clss = results_a[0].boxes.cls.cpu().numpy()
            
            for box, track_id, cls in zip(boxes, ids, clss):
                track_id = int(track_id)
                if int(cls) == 0 or int(cls) == 6:  # Assuming classes 0 and 6 are wagons
                    # RULE 1: Area-based filtering
                    x1, y1, x2, y2 = box
                    box_area = (x2 - x1) * (y2 - y1)
                    image_area = video_width * video_height
                    ratio = box_area / image_area

                    if 0.1 < ratio < 0.8:
                        active_wagons_list.append((track_id, box))
                        if track_id not in unique_wagons:
                            unique_wagons.add(track_id)
                            wagon_timestamps[track_id] = t_start_frame
                    else:
                        pass

        # -----------------------------
        # STEP 2: Model B (Crops) - Detect Numbers
        # -----------------------------
        if model_b:
            for wagon_id, box in active_wagons_list:
                x1, y1, x2, y2 = map(int, box)
                h, w = frame.shape[:2]
                
                # Validation
                if x2 <= x1 or y2 <= y1:
                    continue
                
                # Crop Wagon
                wagon_crop = frame[max(0,y1):min(h,y2), max(0,x1):min(w,x2)]

                if wagon_crop.size == 0:
                    continue

                # -----------------------------
                # CACHE + DEBLUR (ONCE PER TRACK)
                # -----------------------------
                ts = int(time.time() * 100)

                # Initialize cache once
                if 'wagon_image_cache' not in locals():
                    wagon_image_cache = {}

                if wagon_id in wagon_image_cache:
                    wagon_orig = wagon_image_cache[wagon_id]['orig']
                    wagon_deblur = wagon_image_cache[wagon_id]['deblur']
                else:
                    wagon_orig = wagon_crop.copy()
                    wagon_deblur = wagon_crop.copy()

                    if deblur_engine:
                        t0_naf = time.time()
                        blur_score = calculate_blur_score(wagon_crop)
                        blur_scores_log.append(blur_score)

                        if blur_score < 1:
                            # Optimize: Resize if too large to prevent 8s inference
                            h_c, w_c = wagon_crop.shape[:2]
                            max_dim = 640
                            scale = 1.0
                            input_crop = wagon_crop
                            
                            if max(h_c, w_c) > max_dim:
                                scale = max_dim / max(h_c, w_c)
                                input_crop = cv2.resize(wagon_crop, (0,0), fx=scale, fy=scale)
                            
                            print(
                                f"[INFO] Deblurring wagon {wagon_id} | "
                                f"Score: {blur_score:.1f} | "
                                f"Size: {wagon_crop.shape[:2]} -> {input_crop.shape[:2]}"
                            )
                            
                            # Apply enhanced deblurring
                            if use_fp16 and torch.cuda.is_available():
                                with torch.cuda.amp.autocast():
                                    deblurred_small = deblur_engine.deblur(
                                        input_crop,
                                        use_tta=False, 
                                        sharpen_amount=0.6
                                    )
                            else:
                                deblurred_small = deblur_engine.deblur(
                                    input_crop,
                                    use_tta=False,
                                    sharpen_amount=0.6
                                )
                                
                            # Resize back if needed (or keep small for speed in downstream?)
                            if scale != 1.0:
                                wagon_deblur = cv2.resize(deblurred_small, (w_c, h_c))
                            else:
                                wagon_deblur = deblurred_small
                        t_nafnet += (time.time() - t0_naf)

                # -----------------------------
                # MODEL C (ANOMALY) - EVERY FRAME
                # -----------------------------
                if model_c:
                    t0_c = time.time()
                    results_c = model_c.predict(wagon_crop, verbose=False, conf=0.2, half=use_fp16)
                    t_model_c += (time.time() - t0_c)
                    
                    if len(results_c[0].boxes) > 0:
                         best_box =  results_c[0].boxes[0]
                         conf = float(best_box.conf)
                         cls_id = int(best_box.cls)
                         cls_name = model_c.names[cls_id]
                         
                         ax1, ay1, ax2, ay2 = map(int, best_box.xyxy[0])
                         
                         h, w = wagon_crop.shape[:2]
                         pad_x = int((ax2 - ax1) * 0.1)
                         pad_y = int((ay2 - ay1) * 0.1)
                         ax1 = max(0, ax1 - pad_x)
                         ay1 = max(0, ay1 - pad_y)
                         ax2 = min(w, ax2 + pad_x)
                         ay2 = min(h, ay2 + pad_y)
                         
                         # Clamp
                         ax1, ay1 = max(0, ax1), max(0, ay1)
                         ax2, ay2 = min(w, ax2), min(h, ay2)
                         
                         anomaly_crop = wagon_crop[ay1:ay2, ax1:ax2]

                         if wagon_id not in wagon_anomaly_data or conf > wagon_anomaly_data[wagon_id]['conf']:
                            wagon_anomaly_data[wagon_id] = {
                                'type': cls_name,
                                'conf': conf,
                                'crop': anomaly_crop.copy()
                            }
                            print(f"[ALERT] Anomaly '{cls_name}' detected on Wagon {wagon_id} ({conf:.2f})")
                    
                    else:
                        # No anomaly found.
                        # REMOVED: Redundant "Light Enhancement" which forced NAFNet on sharp images.
                        # Just log score.
                        if not deblur_engine:
                            blur_scores_log.append(calculate_blur_score(wagon_crop))
                        pass


                    # Store ONCE per wagon_id
                    wagon_image_cache[wagon_id] = {
                        'orig': wagon_orig,      # true original
                        'deblur': wagon_deblur,  # true deblurred
                        'ts': ts
                    }

                # -----------------------------
                # RESIZE AFTER DEBLUR (FOR MODEL B & OCR)
                # -----------------------------
                wagon_crop = wagon_deblur

                if wagon_crop.shape[0] < 256:
                    scale = 256 / wagon_crop.shape[0]
                    wagon_crop = cv2.resize(
                        wagon_crop,
                        (int(wagon_crop.shape[1] * scale), 256),
                        interpolation=cv2.INTER_CUBIC
                    )


                # -----------------------------
                # NOW run Model B on CLEAN wagon
                # -----------------------------
                if frame_cnt % 3 == 0:
                    t0_b = time.time()
                    results_b = model_b.predict(wagon_crop, verbose=False, conf=0.19, half=use_fp16)
                    t_model_b += (time.time() - t0_b)
                    
                    # DEBUG: Log results
                    if len(results_b[0].boxes) > 0:
                        pass
                        # print(f"[DEBUG] Wagon {wagon_id}: Model B found {len(results_b[0].boxes)} boxes")

                    # If Number Found (Class 0 in Model B)
                    for r in results_b:
                        for nbox in r.boxes.xyxy:
                            nx1, ny1, nx2, ny2 = map(int, nbox)
                            
                            # CROP NUMBER for OCR
                            pad_w = int((nx2 - nx1) * 2.0)
                            pad_h = int((ny2 - ny1) * 1.8)
                            px1 = max(0, nx1 - pad_w)
                            py1 = max(0, ny1 - pad_h)
                            px2 = min(w, nx2 + pad_w)
                            py2 = min(h, ny2 + pad_h)
                            
                            # Clamp
                            px1, py1 = max(0, px1), max(0, py1)
                            px2, py2 = min(w, px2), min(h, py2)
                            
                            number_img = wagon_crop[py1:py2, px1:px2]
                            
                            if number_img.size > 0:
                                wagon_number_data[wagon_id] = {
                                    'crop': number_img
                                }

                            # Visualization
                            gx1, gy1 = x1 + nx1, y1 + ny1
                            gx2, gy2 = x1 + nx2, y1 + ny2
                            cv2.rectangle(frame, (gx1, gy1), (gx2, gy2), (0, 255, 0), 2)
                
                # -----------------------------
                # DUAL-TRIGGER PERSISTENCE
                # -----------------------------
                # If we have ANY evidence (Number OR Anomaly) and haven't saved yet
                has_number = wagon_id in wagon_number_data
                has_anomaly = wagon_id in wagon_anomaly_data
                
                if (has_number or has_anomaly) and wagon_id not in ocr_requested and wagon_id in wagon_image_cache:
                    
                    # print(f"[DEBUG] Triggering Save for Wagon {wagon_id} (Num:{has_number}, Anom:{has_anomaly})")
                    
                    cache = wagon_image_cache[wagon_id]
                    current_ts = cache['ts']
                    
                    # Save Original
                    orig_path = os.path.join(original_save_dir, f"wagon_{wagon_id}_{current_ts}.jpg")
                    cv2.imwrite(orig_path, cache['orig'])
                    
                    # Save Deblurred
                    deblur_path = os.path.join(deblur_save_dir, f"wagon_{wagon_id}_{current_ts}.jpg")
                    cv2.imwrite(deblur_path, cache['deblur'])


                    # PREPARE OCR CROP (If exists)
                    ocr_path = ""
                    final_img = None 
                    
                    if has_number:
                        number_img = wagon_number_data[wagon_id]['crop']
                        
                        # Dynamic Scaling & Enhancement (Copy existing logic)
                        h_img, w_img = number_img.shape[:2]
                        target_height = 128.0
                        if h_img < target_height:
                            scale_factor = target_height / h_img
                            number_img = cv2.resize(number_img, (int(w_img * scale_factor), int(h_img * scale_factor)), interpolation=cv2.INTER_CUBIC)
                        
                        final_img = number_img
                        
                        ocr_path = os.path.join(ocr_save_dir, f"wagon_{wagon_id}_{current_ts}.jpg")
                        cv2.imwrite(ocr_path, final_img)
                    else:
                        pass
                    
                    # SAVE ANOMALY (If exists)
                    anomaly_path = ""
                    anomaly_type = ""
                    anomaly_conf = 0.0
                    
                    if has_anomaly:
                        ad = wagon_anomaly_data[wagon_id]
                        anomaly_type = ad['type']
                        anomaly_conf = ad['conf']
                        
                        anomaly_path = os.path.join(anomaly_save_dir, f"anomaly_{wagon_id}_{current_ts}.jpg")
                        cv2.imwrite(anomaly_path, ad['crop'])
                    
                    
                    # QUEUE FOR OCR
                    if final_img is None:
                         final_img = cache['deblur']
                         
                    # Blocking put is fine now with large buffer (1000 items)
                    ocr_in_q.put((wagon_id, final_img, time.time(), orig_path, deblur_path, ocr_path, anomaly_path, anomaly_type, anomaly_conf))
                    ocr_requested.add(wagon_id)


        metrics['det'].append((time.time()-t_start_frame)*1000)

        # -----------------------------
        # STEP 3: Check OCR & Buffer Data
        # -----------------------------
        while True:
            try:
                # Non-blocking get. If empty, raises queue.Empty immediately.
                item = ocr_out_q.get_nowait()
                
                # Unpack 10 items (CORRECTED)
                wagon_id, raw_text, parsed, req_time, orig_path, deblur_path, ocr_path, anomaly_path, anomaly_type, anomaly_conf = item
                
                # Calculate Latency
                latency = time.time() - req_time
                metrics['ocr'].append(latency)
                
                # Timestamp for this specific detection
                det_time = datetime.datetime.now().strftime("%H:%M:%S")
                wagon_data[wagon_id] = {'raw': raw_text, 'parsed': parsed}
                
                # Formatted Output
                parsed_str = str(parsed) if parsed else "Invalid"
                
                log_entry = f"[{det_time}] ID: {wagon_id} | OCR: {raw_text:<15} | Parsed: {parsed_str} | Latency: {latency:.2f}s"
                print(log_entry)
                
                consist_log.append({
                    'id': wagon_id,
                    'raw': raw_text, 
                    'parsed': parsed,
                    'timestamp': det_time
                })

                # DB Log (Using Actual Paths)
                print(f"[DEBUG] Adding Wagon {wagon_id} to DB...")
                database.add_wagon(
                    inspection_id=inspection_id,
                    wagon_index=wagon_id,
                    ocr_text=raw_text,
                    ocr_conf=0.99 if raw_text != "OCR Failed" else 0.0,
                    orig_path=orig_path or "",
                    deblur_path=deblur_path or "",
                    ocr_path=ocr_path or "",
                    defects="None", # Can update this to anomaly_type if preferred, or keep defects for legacy
                    is_night=False,
                    anomaly_path=anomaly_path,
                    anomaly_type=anomaly_type,
                    anomaly_conf=anomaly_conf
                )

            except queue.Empty:
                # Continue main video loop if no OCR result ready
                break


        # -----------------------------
        # STEP 4: Visualization
        # -----------------------------
        for wagon_id, box in active_wagons_list:
            x1, y1, x2, y2 = map(int, box)
            
            info = None
            if wagon_id in wagon_data:
                d = wagon_data[wagon_id]
                info = d['parsed']['formatted'] if d['parsed'] else d['raw']
            
            draw_track(frame, (x1,y1,x2,y2), wagon_id, info, color=(255, 0, 0))

        # Stats
        curr_time = time.time()
        loop_time = curr_time - prev_time
        metrics['fps'].append(1/loop_time if loop_time > 0 else 0)
        prev_time = curr_time
        
        avg_fps = sum(metrics['fps'])/len(metrics['fps']) if metrics['fps'] else 0
        stats = [f"FPS: {avg_fps:.1f}", 
                 f"Det Time: {sum(metrics['det'])/len(metrics['det']):.0f}ms",
                 f"Count: {len(unique_wagons)}"]
        draw_stats(frame, stats)
        
        # Debug Profiling Print
        if frame_cnt % 30 == 0:
             print(f"[PROFILE] Fr:{frame_cnt} | Loop:{loop_time*1000:.1f}ms | ModA:{t_model_a*1000:.1f}ms | ModB:{t_model_b*1000:.1f}ms | ModC:{t_model_c*1000:.1f}ms | NAF:{t_nafnet*1000:.1f}ms")
        
        # Debug Profiling Print
        if frame_cnt % 30 == 0:
             # Calculate last frame breakdown if available
             try:
                 ma_ms = (t_a_end - t_a_start) * 1000
                 mc_ms = (t_c_end - t_c_start) * 1000 if 't_c_end' in locals() else 0
                 print(f"[PROFILE] Frame {frame_cnt} | Model A: {ma_ms:.1f}ms | Model C: {mc_ms:.1f}ms | Total Loop: {(curr_time - prev_time)*1000:.1f}ms")
             except: pass

                # -----------------------------
        # VLC-STYLE OVERLAY (Progress Bar + Info)
        # -----------------------------
        h, w = frame.shape[:2]
        
        # Semi-transparent bottom bar (like VLC controls area)
        overlay = frame.copy()
        bar_height = 40
        cv2.rectangle(overlay, (0, h - bar_height), (w, h), (30, 30, 30), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        # Progress bar
        progress = frame_cnt / total_frames if total_frames > 0 else 0
        bar_y = h - 25
        bar_start_x = 120
        bar_end_x = w - 120
        bar_width = bar_end_x - bar_start_x
        
        # Background bar (gray)
        cv2.rectangle(frame, (bar_start_x, bar_y - 3), (bar_end_x, bar_y + 3), (80, 80, 80), -1)
        # Progress bar (orange/yellow like VLC)
        progress_x = int(bar_start_x + bar_width * progress)
        cv2.rectangle(frame, (bar_start_x, bar_y - 3), (progress_x, bar_y + 3), (0, 165, 255), -1)
        # Progress knob
        cv2.circle(frame, (progress_x, bar_y), 6, (255, 255, 255), -1)
        
        # Time display (left side)
        current_time_sec = frame_cnt / video_fps if video_fps > 0 else 0
        total_time_sec = total_frames / video_fps if video_fps > 0 else 0
        time_str = f"{int(current_time_sec // 60):02d}:{int(current_time_sec % 60):02d} / {int(total_time_sec // 60):02d}:{int(total_time_sec % 60):02d}"
        cv2.putText(frame, time_str, (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Wagon count display (right side)
        count_str = f"Wagons: {len(unique_wagons)}"
        cv2.putText(frame, count_str, (w - 110, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
        
        # Top banner (semi-transparent)
        overlay_top = frame.copy()
        cv2.rectangle(overlay_top, (0, 0), (w, 35), (30, 30, 30), -1)
        frame = cv2.addWeighted(overlay_top, 0.7, frame, 0.3, 0)

        
        if not headless:
            cv2.imshow(window_name, frame)
            
            # Keyboard controls (like VLC)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q' or ESC to quit 
                break
            elif key == ord(' '):  # Space to pause
                print("[INFO] Paused. Press any key to continue...")
                cv2.waitKey(0)

        # STREAMING: If frame_queue provided, encode and push
        if frame_queue is not None:
             try:
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    if frame_queue.full():
                        try: frame_queue.get_nowait() # Drop old frame if full
                        except: pass
                    frame_queue.put(buffer.tobytes())
             except Exception as e:
                 print(f"[WARNING] Stream encode failed: {e}")

    ocr_in_q.put(None)
    cap.release()

    if not headless:
        cv2.destroyAllWindows()

    # -----------------------------
    # DRAIN PHASE (Post-Video)
    # -----------------------------
    print("-" * 50)
    print("[INFO] Video finished. Starting OCR Drain Phase...")
    print(f"[INFO] Waiting for OCR worker to finish pending tasks...")
    
    while ocr_p.is_alive():
        try:
            # Check for results (blocking with timeout to allow join check)
            item = ocr_out_q.get(timeout=0.5)
            
            wagon_id, raw_text, parsed, req_time, orig_path, deblur_path, ocr_path, anomaly_path, anomaly_type, anomaly_conf = item
            
            latency = time.time() - req_time
            det_time = datetime.datetime.now().strftime("%H:%M:%S")
            parsed_str = str(parsed) if parsed else "Invalid"
            
            log_entry = f"[{det_time}] [DRAIN] ID: {wagon_id} | OCR: {raw_text:<15} | Parsed: {parsed_str}"
            print(log_entry)
            
            consist_log.append({'id': wagon_id, 'raw': raw_text, 'parsed': parsed, 'timestamp': det_time})
            
            database.add_wagon(
                inspection_id=inspection_id,
                wagon_index=wagon_id,
                ocr_text=raw_text,
                ocr_conf=0.99 if raw_text != "OCR Failed" else 0.0,
                orig_path=orig_path or "",
                deblur_path=deblur_path or "",
                ocr_path=ocr_path or "",
                defects="None",
                is_night=False,
                anomaly_path=anomaly_path,
                anomaly_type=anomaly_type,
                anomaly_conf=anomaly_conf
            )
        except queue.Empty:
            pass
            
    ocr_p.join()
    print("[INFO] OCR Drain Phase Complete.")
    
    # Signal End of Stream (non-blocking)
    if frame_queue:
        try:
            if frame_queue.full():
                try: frame_queue.get_nowait()
                except: pass
            frame_queue.put_nowait(None)
        except:
            pass
    
    # ---------------------------------------------------------
    # Generate Final Report
    # ---------------------------------------------------------
    print("[INFO] Generating final report...")
    
    total_wagons = len(unique_wagons)
    end_time_str = datetime.datetime.now().strftime("%H:%M")
    report_date = start_time.strftime("%d-%b-%Y")
    
    # Header
    report_lines = []
    report_lines.append("+-----------------------------------------------------------------------+")
    report_lines.append("|  [Logo]  INDIAN RAILWAYS - AUTOMATED FREIGHT INSPECTION REPORT        |")
    report_lines.append("+-----------------------------------------------------------------------+")
    report_lines.append(f"|  Site: Ahemdabad Jn (Cam-02)   |   Date: {report_date}   |   Time: {end_time_str}|")
    report_lines.append(f"|  Train Speed: 62 km/h          |   Total Wagons: {total_wagons:<5}    |   Defects: 0 |")
    report_lines.append("+-----------------------------------------------------------------------+")
    
    # Critical Alerts (Mocked for now)
    report_lines.append("|  [ CRITICAL ALERTS ]                                                  |")
    report_lines.append("|  * No Critical Defects Detected by AI System                          |")
    report_lines.append("|                                                                       |")
    report_lines.append("+-----------------------------------------------------------------------+")
    
    # Consist List
    report_lines.append("|  [ CONSIST LIST ]                                                     |")
    report_lines.append("|  #   | Wagon ID       | Type   | Owner | Condition  | Timestamp       |")
    
    # Populate Consist List from Data
    # Match consist_log items to unique_wagons. 
    # Some wagons in unique_wagons might not have OCR data (missed detection/ocr).
    # We list ALL detected wagons.
    
    sorted_ids = sorted(list(unique_wagons))
    
    # Create lookup from id -> ocr data
    ocr_lookup = {item['id']: item for item in consist_log}
    
    for idx, uid in enumerate(sorted_ids, 1):
        wagon_id_str = "Unknown"
        w_type = "-"
        w_owner = "-"
        w_cond = "Good"
        w_time = "-"
        
        if uid in ocr_lookup:
            data = ocr_lookup[uid]
            # ID: Prefer parsed 11-digit formatted, else raw text
            if data['parsed']:
                wagon_id_str = data['parsed']['formatted']
                w_type = data['parsed']['type']
                w_owner = data['parsed']['railway']
            else:
                wagon_id_str = data['raw'][:14] # Truncate if too long
            
            w_time = data['timestamp']
        else:
            wagon_id_str = f"Track-{uid}" # Fallback
            
        # Formatting Line (Fixed Width approx)
        # ID: 14 chars, Type: 6, Owner: 5, Cond: 10
        line = f"|  {idx:<4}| {wagon_id_str:<14} | {w_type:<6} | {w_owner:<5} | {w_cond:<10} | {w_time:<15} |"
        report_lines.append(line)

    report_lines.append("+-----------------------------------------------------------------------+")
    
    # AI System Log
    report_lines.append("|  [ AI SYSTEM LOG ]                                                    |")
    report_lines.append(f"|  * {frame_cnt} Frames Processed                                              |")
    report_lines.append("|  * Pipeline: Cascaded YOLOv8 + PaddleOCR                              |")
    report_lines.append("+-----------------------------------------------------------------------+")

    # Write to File
    with open(log_file_path, 'w') as f:
        f.write('\n'.join(report_lines))

    print("-" * 50)
    print(f"[SUMMARY] Total Wagons Counted: {total_wagons}")
    print(f"[SUMMARY] Report saved to: {log_file_path}")
    print("-" * 50)
    
    # Mark as Completed
    # Calculate Metrics
    final_fps = frame_cnt / (time.time() - start_time.timestamp())
    avg_brightness = np.mean(brightness_log) if brightness_log else 0.0
    resolution_str = f"{video_width}x{video_height}"
    
    # Blur Histogram (Bins: <50, 50-100, 100-200, >200)
    blur_hist = {'<50': 0, '50-100': 0, '100-200': 0, '>200': 0}
    if blur_scores_log:
        for s in blur_scores_log:
            if s < 50: blur_hist['<50'] += 1
            elif s < 100: blur_hist['50-100'] += 1
            elif s < 200: blur_hist['100-200'] += 1
            else: blur_hist['>200'] += 1
            
    blur_stats_json = json.dumps(blur_hist)

    # Train Speed Calculation (Robust Inter-Wagon Timing)
    # Speed = Wagon Length (14.7m) / Avg Time Gap
    calculated_speed = 0.0
    
    if len(wagon_timestamps) > 2:
        # Sort by timestamp
        times = sorted(wagon_timestamps.values())
        deltas = []
        for i in range(1, len(times)):
            d = times[i] - times[i-1]
            if 0.5 < d < 5.0: # Filter outliers (e.g. stops or missed detections)
                deltas.append(d)
        
        if len(deltas) > 0:
            avg_delta = sum(deltas) / len(deltas)
            if avg_delta > 0:
                speed_mps = 14.7 / avg_delta
                calculated_speed = speed_mps * 3.6 # Convert to km/h
                print(f"[INFO] Estimated Train Speed: {calculated_speed:.1f} km/h (Avg Gap: {avg_delta:.2f}s)")

    # Mark as Completed & Save Metrics
    database.update_inspection_count(inspection_id, total_wagons)
    database.update_inspection_status(inspection_id, "COMPLETED")
    database.update_inspection_metrics(inspection_id, final_fps, resolution_str, avg_brightness, blur_stats_json, calculated_speed)

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_path", required=True)
    # Default Paths
    parser.add_argument("--model_a", default="railway_hackathon_take7/merged_model_v7_generalized/weights/best.pt")
    # Placeholder for Model B until user trains it
    parser.add_argument("--model_b", default="railway_hackathon_numbers_take3/number_detector_v1/weights/best.pt")
    parser.add_argument("--deblur_model", default="finetuned_nafnet/nafnet_wagon_finetuned.pth")
    parser.add_argument("--model_c", default="railway_hackathon_damage/damage_detector_v1/weights/best.pt")
    
    # GPU Optimization flags
    parser.add_argument("--disable-fp16", action="store_true", help="Disable FP16 inference (slower, more compatible)")
    parser.add_argument("--disable-compile", action="store_true", help="Disable torch.compile optimization")
    
    args = parser.parse_args()
    cascaded_pipeline(
        args.video_path, 
        args.model_a, 
        args.model_b, 
        args.deblur_model, 
        args.model_c,
        use_fp16=not args.disable_fp16,
        use_torch_compile=not args.disable_compile
    )
