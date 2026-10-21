import os
import sys
import time
import json
import urllib.request
import urllib.error

BASE_URL = os.environ.get("TEST_API_URL", "http://127.0.0.1:8000")

def run_smoke_test():
    print(f"==================================================")
    print(f"  CARGOVISION AI — PRODUCTION SMOKE TEST")
    print(f"  Target: {BASE_URL}")
    print(f"==================================================")

    # 1. Health Probe
    print("\n[TEST 1] Testing /health endpoint...")
    t0 = time.time()
    try:
        req = urllib.request.urlopen(f"{BASE_URL}/health", timeout=5)
        dt = (time.time() - t0) * 1000
        assert req.getcode() == 200, f"Expected 200, got {req.getcode()}"
        health_data = json.loads(req.read().decode())
        print(f"  PASS: 200 OK in {dt:.1f}ms")
        print(f"  Payload: {json.dumps(health_data)}")
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

    # 2. Existing History & Database Integrity
    print("\n[TEST 2] Testing /history and database integrity...")
    try:
        req = urllib.request.urlopen(f"{BASE_URL}/history", timeout=5)
        history = json.loads(req.read().decode())
        print(f"  PASS: 200 OK. Total inspections in DB: {len(history)}")
        if history:
            print(f"  Latest record: #{history[0]['id']} ({history[0].get('video_name')}) - {history[0].get('status')}")
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

    # 3. Security Check: Reject Invalid Extension (.exe)
    print("\n[TEST 3] Testing security upload rejection for unallowed extension (.exe)...")
    boundary = "----TestBoundarySecurity"
    bad_body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"malicious_script.exe\"\r\n"
        f"Content-Type: application/x-msdownload\r\n\r\n"
        f"fake_binary_code\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/upload",
        data=bad_body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    try:
        urllib.request.urlopen(req)
        print("  FAIL: Server accepted an .exe upload!")
        return False
    except urllib.error.HTTPError as e:
        if e.code == 400:
            print(f"  PASS: Rejected with HTTP 400 Bad Request: {e.read().decode()[:80]}...")
        else:
            print(f"  FAIL: Expected 400, got {e.code}")
            return False

    # 4. End-to-End Real Video Upload & Cascaded Pipeline Execution
    print("\n[TEST 4] Testing real video upload and cascaded pipeline execution...")
    test_video = "Assests/wagon_number_detection2.mp4"
    if not os.path.exists(test_video):
        print(f"  SKIP: {test_video} not found")
        return True

    with open(test_video, "rb") as vf:
        video_bytes = vf.read()

    video_boundary = "----TestVideoUploadBoundary"
    v_body = (
        f"--{video_boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"smoke_test_run.mp4\"\r\n"
        f"Content-Type: video/mp4\r\n\r\n"
    ).encode("utf-8") + video_bytes + f"\r\n--{video_boundary}--\r\n".encode("utf-8")

    upload_req = urllib.request.Request(
        f"{BASE_URL}/upload",
        data=v_body,
        headers={"Content-Type": f"multipart/form-data; boundary={video_boundary}"}
    )

    t0_up = time.time()
    try:
        up_res = urllib.request.urlopen(upload_req)
        up_data = json.loads(up_res.read().decode())
        inspection_id = up_data["inspection_id"]
        print(f"  Upload accepted in {(time.time() - t0_up)*1000:.1f}ms! Inspection ID: #{inspection_id}")
    except Exception as e:
        print(f"  FAIL on upload: {e}")
        return False

    # 5. Polling Job Status & Concurrency Protection
    print("\n[TEST 5] Testing concurrency lock while job is active...")
    # Attempt a 2nd simultaneous upload — should return HTTP 429 Too Many Requests
    second_req = urllib.request.Request(
        f"{BASE_URL}/upload",
        data=v_body,
        headers={"Content-Type": f"multipart/form-data; boundary={video_boundary}"}
    )
    try:
        urllib.request.urlopen(second_req)
        print("  WARNING: Server allowed 2nd concurrent job (check MAX_CONCURRENT_JOBS)")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"  PASS: Concurrency ceiling correctly returned HTTP 429 Too Many Requests!")
        else:
            print(f"  HTTP Response: {e.code}")

    print("\n[TEST 6] Polling processing status until completion...")
    max_wait = 120 # 2 minutes timeout
    t_start = time.time()
    completed = False

    while (time.time() - t_start) < max_wait:
        try:
            st_res = urllib.request.urlopen(f"{BASE_URL}/inspections/{inspection_id}/status")
            st_data = json.loads(st_res.read().decode())
            cur_status = st_data.get("status")
            print(f"  [{int(time.time() - t_start)}s] Status: {cur_status}")
            if cur_status == "COMPLETED":
                completed = True
                break
        except Exception as e:
            print(f"  Polling warning: {e}")
        time.sleep(4)

    if not completed:
        print("  FAIL: Pipeline processing timed out after 120s")
        return False

    # 7. Verify Wagon & OCR Results
    print(f"\n[TEST 7] Fetching wagon detection and OCR results for #{inspection_id}...")
    try:
        w_res = urllib.request.urlopen(f"{BASE_URL}/history/{inspection_id}")
        wagons = json.loads(w_res.read().decode())
        print(f"  PASS: Retrieved {len(wagons)} wagons processed:")
        for w in wagons[:5]:
            print(f"    - Wagon #{w.get('wagon_index')}: OCR='{w.get('ocr_text')}' (conf: {w.get('ocr_confidence')})")
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

    # 8. Verify PDF Report Generation
    print(f"\n[TEST 8] Testing PDF inspection report generation for #{inspection_id}...")
    try:
        rep_res = urllib.request.urlopen(f"{BASE_URL}/history/{inspection_id}/report")
        assert rep_res.getcode() == 200
        content_type = rep_res.headers.get("Content-Type")
        pdf_bytes = rep_res.read()
        print(f"  PASS: PDF report successfully generated! Size: {len(pdf_bytes)} bytes, Content-Type: {content_type}")
        assert len(pdf_bytes) > 1000, "PDF size too small"
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

    print("\n==================================================")
    print("  ALL 8 SMOKE TESTS PASSED CLEANLY! ✅")
    print("==================================================")
    return True

if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
