from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import yt_dlp
import uvicorn
import asyncio
import random
import time
import os
import sys
from datetime import datetime

# Import Database Module
sys.path.append(os.path.join(os.path.dirname(__file__), '../core'))
import database
import report_generator
import ai_search
# Trigger Reload (Query Fix)
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel


# Import Pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), '../scripts'))
from cascaded_pipeline import cascaded_pipeline

from cascaded_pipeline import cascaded_pipeline
import multiprocessing as mp

app = FastAPI(
    title="CargoVision AI",
    description="CargoVision AI — Intelligent Railway Wagon Inspection API",
    version="1.0.0"
)

MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", 35))
MAX_CONCURRENT_JOBS = int(os.environ.get("MAX_CONCURRENT_JOBS", 1))
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
active_job_count = 0

def resolve_model_path(base_dir, candidate_rel_paths):
    """Resolve model path against available files with fallback and MODEL_DIR support."""
    model_dir_env = os.environ.get("MODEL_DIR")
    if model_dir_env and os.path.exists(model_dir_env):
        for rel_path in candidate_rel_paths:
            fname = os.path.basename(rel_path)
            p = os.path.join(model_dir_env, fname)
            if os.path.exists(p):
                return p

    for rel_path in candidate_rel_paths:
        p = os.path.join(base_dir, rel_path)
        if os.path.exists(p):
            return p
    return os.path.join(base_dir, candidate_rel_paths[0])

@app.get("/")
@app.get("/health")
async def health_check():
    """Health check endpoint providing readiness and resource status."""
    db_ok = os.path.exists(database.DB_PATH)
    return {
        "status": "healthy",
        "service": "CargoVision AI",
        "version": "1.0.0",
        "environment": os.environ.get("ENV", "development"),
        "database": "connected" if db_ok else "initialized",
        "active_jobs": active_job_count,
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "max_upload_size_mb": MAX_UPLOAD_SIZE_MB
    }

# Registry for Active Processing Streams
# Format: { inspection_id: mp.Queue }
active_process_streams = {}

# Initialize DB (Run Migrations)
database.init_db()

# Enable environment-driven CORS for frontend
cors_origins_env = os.environ.get("CORS_ORIGINS")
if cors_origins_env:
    allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Serve Static Files (Images)
# The pipeline saves images to:
# - .../full model/detection
# - .../full model/DeblurredImg
# - .../full model/OriginalImg
# - .../full model/OCRimage
# We mount the 'full model' parent directory (project root) so we can access all of them.
# Fix: Use '../../' to go to root. Do NOT append 'full model' again.
full_model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
os.makedirs(full_model_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=full_model_dir), name="static")

# Global Mock Data (Still used for live stats for now)
mock_stats = {
    "total_wagons": 0,
    "last_wagon_id": "N/A",
    "defects_found": 0,
    "status": "Idle"
}

# ... (YouTube functions remain same, skipping for brevity in this replace block if possible, but replace_file_content replaces chunks)
# I will keep the existing imports and setup, just adding the new routes.

@app.get("/history")
async def get_history():
    """Get list of all past inspections."""
    return database.get_all_inspections()

def run_pipeline_with_tracking(video_path, model_a, model_b, deblur_model, model_c, inspection_id, stream_queue):
    """Run pipeline and ensure active job count is decremented on completion or failure."""
    global active_job_count
    try:
        cascaded_pipeline(
            video_path=video_path,
            model_a_path=model_a,
            model_b_path=model_b,
            deblur_model_path=deblur_model,
            model_c_path=model_c,
            headless=True,
            inspection_id=inspection_id,
            frame_queue=stream_queue
        )
    finally:
        active_job_count = max(0, active_job_count - 1)

@app.post("/upload")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a video and automatically trigger processing with security controls."""
    global active_job_count
    
    # 1. Concurrency Control
    if active_job_count >= MAX_CONCURRENT_JOBS:
        raise HTTPException(
            status_code=429,
            detail=f"Inspection pipeline is currently at maximum capacity ({active_job_count}/{MAX_CONCURRENT_JOBS} active jobs). Please wait for the current inspection to complete."
        )

    # 2. File Format / Extension Validation
    orig_name = file.filename or "upload.mp4"
    ext = os.path.splitext(orig_name)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed video formats: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}"
        )

    # 3. Path Traversal & Safe Filename Handling
    safe_base = os.path.basename(orig_name)
    timestamp_prefix = int(time.time())
    safe_filename = f"{timestamp_prefix}_{safe_base}"

    try:
        # Define Storage Paths
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../full model'))
        upload_dir_env = os.environ.get("UPLOAD_DIR")
        video_dir = upload_dir_env if upload_dir_env else os.path.join(base_dir, 'Video')
        os.makedirs(video_dir, exist_ok=True)
        
        file_path = os.path.join(video_dir, safe_filename)
        
        # 4. Chunked Streaming with Size Limit Enforcement
        total_bytes = 0
        max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
        
        with open(file_path, "wb") as f:
            while chunk := await file.read(1024 * 1024): # 1 MB chunks
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    f.close()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed upload size of {MAX_UPLOAD_SIZE_MB} MB."
                    )
                f.write(chunk)
            
        print(f"[API] Video successfully saved to: {file_path} ({total_bytes / (1024*1024):.2f} MB)")
        
        # Define Model Paths with smart resolution
        model_a = resolve_model_path(base_dir, [
            "railway_hackathon_take7/merged_model_v7_generalized/weights/best.pt",
            "railway_hackathon_take6/merged_model_v6_generalized/weights/best.pt",
            "railway_hackathon_take5/merged_model_v4/weights/best.pt",
            "yolov8n.pt"
        ])
        model_b = resolve_model_path(base_dir, [
            "railway_hackathon_numbers_take3/number_detector_v1/weights/best.pt",
            "railway_hackathon_numbers/number_detector_v1/weights/best.pt",
            "yolov8n.pt"
        ])
        model_c = resolve_model_path(base_dir, [
            "railway_hackathon_damage/damage_detector_v1/weights/best.pt"
        ])
        deblur_model = resolve_model_path(base_dir, [
            "finetuned_nafnet/nafnet_wagon_finetuned.pth",
            "NAFnet/NAFNet-GoPro-width32.pth"
        ])
        
        # Create Inspection Record BEFORE processing (so frontend has an ID)
        inspection_id = database.create_inspection(safe_filename)
        
        # Create Queue for Streaming (Max size to prevent memory bloom)
        stream_queue = mp.Manager().Queue(maxsize=10)
        active_process_streams[inspection_id] = stream_queue

        # Increment active job counter
        active_job_count += 1

        # Trigger Pipeline in Background with safety wrapper
        background_tasks.add_task(
            run_pipeline_with_tracking,
            video_path=file_path,
            model_a=model_a,
            model_b=model_b,
            deblur_model=deblur_model,
            model_c=model_c,
            inspection_id=inspection_id,
            stream_queue=stream_queue
        )
        
        return {
            "message": "Upload successful. Processing started in background.", 
            "filename": safe_filename,
            "inspection_id": inspection_id,
            "status": "PROCESSING"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during upload: {e}")
        return Response(content=f"Upload failed: {str(e)}", status_code=500)

@app.get("/inspections/{inspection_id}/status")
async def get_inspection_status(inspection_id: int):
    """Check the status of a specific inspection."""
    insp = database.get_inspection_by_id(inspection_id)
    if not insp:
        return Response(content="Inspection not found", status_code=404)
    
    # If status column missing (migration edge case), assume completed if wagons exist?
    # Or just default to COMPLETED if not PROCESSING?
    status = insp.get('status', 'COMPLETED') 
    return {"status": status}


@app.get("/history/{inspection_id}/report")
async def generate_report_pdf(inspection_id: int):
    """Generate and download PDF report for an inspection."""
    inspection = database.get_inspection_by_id(inspection_id)
    if not inspection:
        return Response(content="Inspection not found", status_code=404)
        
    wagons = database.get_wagons_for_inspection(inspection_id)
    
    # Generate PDF
    pdf = report_generator.generate_report(inspection, wagons)
    
    # Output to bytes
    # The .output() method returns a bytearray in newer FPDF versions
    pdf_bytes = pdf.output(dest='S')
    
    # Convert to bytes if it's a bytearray
    if isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    elif isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin1')
    
    headers = {
        'Content-Disposition': f'attachment; filename="report_{inspection_id}.pdf"'
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

@app.get("/history/{inspection_id}")
async def get_inspection_details(inspection_id: int):
    """Get all wagons for a specific inspection."""
    wagons = database.get_wagons_for_inspection(inspection_id)
    
    clean_wagons = []
    for w in wagons:
        w_dict = dict(w)
        # Convert absolute path to static URL
        # Logic: find 'full model' in path and take everything after it
        for key in ['original_image_path', 'deblurred_image_path', 'cropped_number_path', 'anomaly_image_path']:
             # Note: API might return keys slightly differently depending on DB row factory
             # But let's assume keys match schema
            val = w_dict.get(key)
            if val and isinstance(val, str) and 'full model' in val:
                # abs_path: C:\Users\dhruv\...\full model\DeblurredImg\wagon_1_123.jpg
                # rel_path: DeblurredImg/wagon_1_123.jpg
                
                # Split by 'full model' (ignoring case if possible, but usually FS matches)
                # We use simple split assuming standard installation
                parts = val.split('full model')
                if len(parts) > 1:
                    rel_path = parts[-1].replace('\\', '/').lstrip('/')
                    w_dict[key] = f"http://localhost:8000/static/{rel_path}"
        
        clean_wagons.append(w_dict)
        
    return clean_wagons

@app.get("/stats")
async def get_stats():
    return mock_stats

@app.get("/api/analytics")
async def get_analytics():
    """Get analytics data aggregated by date for the Analysis page."""
    try:
        analytics_data = database.get_analytics_data()
        return analytics_data
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        return Response(content=f"Failed to fetch analytics: {str(e)}", status_code=500)



class SearchRequest(BaseModel):
    query: str
    # api_key: str  <-- Removed, using server-side key

@app.post("/api/search")
async def search_endpoint(request: SearchRequest):
    """
    Execute an AI-powered search query against the database.
    """
    # Key check removed here, handled in service
        
    try:
        service = ai_search.AISearchService() # Uses global key
        result = service.execute_search(request.query)
        return result
    except Exception as e:
        return {"error": str(e)}

def get_youtube_stream_url(youtube_url: str) -> str:
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info["url"]


async def generate_frames(url_key: int, request: Request):
    """Generator function to stream video frames from a YouTube URL."""
    urls = {
        1: "https://www.youtube.com/watch?v=7xdHH9KMSVk",
        2: "https://www.youtube.com/watch?v=nO81bQFql7M",
        3: "https://www.youtube.com/watch?v=23tmCNeFh7A"
    }
    youtube_url = urls.get(url_key, urls[1])
    cap = None
    try:
        stream_url = get_youtube_stream_url(youtube_url)
        cap = cv2.VideoCapture(stream_url)
        loop = asyncio.get_running_loop()
        
        while True:
            # Check if the client has disconnected
            if await request.is_disconnected():
                print(f"Client disconnected for stream {url_key}. Stopping.")
                break

            # Run blocking I/O (cap.read) in a separate thread to avoid blocking the event loop
            success, frame = await loop.run_in_executor(None, cap.read)

            if not success:
                print(f"Stream {url_key} ended or failed. Breaking loop.")
                break

            # Also run the potentially blocking encoding in an executor
            ret, buffer = await loop.run_in_executor(None, cv2.imencode, '.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            await asyncio.sleep(0.04)  # Use asyncio.sleep for non-blocking delay
    except Exception as e:
        # This will catch errors like client disconnection during the yield
        print(f"An error occurred in generate_frames for stream {url_key} (client likely disconnected): {e}")
    finally:
        if cap:
            print(f"Releasing video capture for stream {url_key}.")
            cap.release()

@app.get("/video_feed/{stream_id}")
async def video_feed(stream_id: int, request: Request):
    return StreamingResponse(generate_frames(stream_id, request), media_type="multipart/x-mixed-replace; boundary=frame")


# -----------------------------
# PROCESSING PREVIEW STREAM
# -----------------------------
async def generate_processing_frames(inspection_id: int, request: Request):
    """Generator to stream frames from an active processing pipeline."""
    if inspection_id not in active_process_streams:
        # If no active stream, maybe return a placeholder or stop
        return

    q = active_process_streams[inspection_id]
    
    try:
        while True:
            if await request.is_disconnected():
                break
                
            try:
                # Non-blocking check
                frame_bytes = q.get_nowait()
                
                if frame_bytes is None: # Sentinel for end
                    break
                    
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                await asyncio.sleep(0.01) # Small sleep to yield control
            except:
                # Queue empty, wait a bit
                await asyncio.sleep(0.05)
                
    except Exception as e:
        print(f"Error in processing stream {inspection_id}: {e}")
    finally:
        # Cleanup if job done (optional, but good practice)
        pass

@app.get("/stream/processing/{inspection_id}")
async def stream_processing_feed(inspection_id: int, request: Request):
    return StreamingResponse(generate_processing_frames(inspection_id, request), media_type="multipart/x-mixed-replace; boundary=frame")


# -----------------------------
# LIVE PROCESSING CONTROL
# -----------------------------
live_process = None
live_inspection_id = None

import multiprocessing

def run_live_pipeline(stream_url, inspection_id):
    """Wrapper to run the pipeline in a separate process."""
    # Define Model Paths with smart resolution
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../full model'))
    model_a = resolve_model_path(base_dir, [
        "railway_hackathon_take7/merged_model_v7_generalized/weights/best.pt",
        "railway_hackathon_take6/merged_model_v6_generalized/weights/best.pt",
        "railway_hackathon_take5/merged_model_v4/weights/best.pt",
        "yolov8n.pt"
    ])
    model_b = resolve_model_path(base_dir, [
        "railway_hackathon_numbers_take3/number_detector_v1/weights/best.pt",
        "railway_hackathon_numbers/number_detector_v1/weights/best.pt",
        "yolov8n.pt"
    ])
    model_c = resolve_model_path(base_dir, [
        "railway_hackathon_damage/damage_detector_v1/weights/best.pt"
    ])
    deblur_model = resolve_model_path(base_dir, [
        "finetuned_nafnet/nafnet_wagon_finetuned.pth",
        "NAFnet/NAFNet-GoPro-width32.pth"
    ])
    
    # Run Pipeline
    # Note: cascaded_pipeline handles DB connections internally
    cascaded_pipeline(
        video_path=stream_url,
        model_a_path=model_a,
        model_b_path=model_b,
        deblur_model_path=deblur_model,
        model_c_path=model_c,
        headless=True,
        inspection_id=inspection_id
    )

@app.post("/live/start")
async def start_live_processing(stream_id: int = 1):
    """Start the AI pipeline on the live stream."""
    global live_process, live_inspection_id
    
    if live_process and live_process.is_alive():
        return {"status": "error", "message": "Live processing is already running."}
    
    # Get Stream URL
    urls = {
        1: "https://www.youtube.com/watch?v=7xdHH9KMSVk",
        2: "https://www.youtube.com/watch?v=nO81bQFql7M",
        3: "https://www.youtube.com/watch?v=23tmCNeFh7A"
    }
    youtube_url = urls.get(stream_id, urls[1])
    try:
        stream_url = get_youtube_stream_url(youtube_url)
    except Exception as e:
        return {"status": "error", "message": f"Failed to get stream URL: {e}"}
        
    # Create Inspection Record
    video_name = f"Live Stream {stream_id} - {datetime.now().strftime('%H:%M')}"
    live_inspection_id = database.create_inspection(video_name)
    database.update_inspection_times(live_inspection_id, start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Start Process
    live_process = multiprocessing.Process(
        target=run_live_pipeline, 
        args=(stream_url, live_inspection_id)
    )
    live_process.start()
    
    print(f"[API] Live processing started. PID: {live_process.pid} | Inspection ID: {live_inspection_id}")
    
    return {
        "status": "started", 
        "inspection_id": live_inspection_id, 
        "message": "AI Pipeline attached to live feed."
    }

@app.post("/live/stop")
async def stop_live_processing():
    """Stop the AI pipeline."""
    global live_process, live_inspection_id
    
    if live_process and live_process.is_alive():
        print(f"[API] Stopping live processing process {live_process.pid}...")
        live_process.terminate()
        live_process.join()  # Wait for it to finish
        live_process = None
        
        # Update DB
        if live_inspection_id:
            database.update_inspection_times(live_inspection_id, end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            database.update_inspection_status(live_inspection_id, "COMPLETED") 
            # Note: Might leave metrics empty if pipeline didn't finish gracefully, 
            # but that's acceptable for forced stop.
        
        return {"status": "stopped", "message": "Live processing stopped."}
    
    return {"status": "idle", "message": "No active processing to stop."}

@app.get("/live/status")
async def get_live_status():
    """Check if live processing is active."""
    global live_process, live_inspection_id
    is_running = live_process is not None and live_process.is_alive()
    return {
        "is_running": is_running,
        "inspection_id": live_inspection_id if is_running else None
    }

@app.get("/stats")
async def get_stats():
    return mock_stats

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
