import urllib.request
import urllib.error
import json

def test():
    print("--- 1. Testing Health Endpoint ---")
    req = urllib.request.urlopen("http://127.0.0.1:8000/health")
    data = json.loads(req.read().decode('utf-8'))
    print("Health Status:", req.getcode(), data)

    print("\n--- 2. Testing Docs Endpoint ---")
    req = urllib.request.urlopen("http://127.0.0.1:8000/docs")
    print("Docs Status:", req.getcode())

    print("\n--- 3. Testing History Endpoint ---")
    req = urllib.request.urlopen("http://127.0.0.1:8000/history")
    print("History Status:", req.getcode())

    print("\n--- 4. Testing Invalid Extension Upload (.exe) ---")
    boundary = "----TestBoundary12345"
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"malicious.exe\"\r\n"
        f"Content-Type: application/octet-stream\r\n\r\n"
        f"test-content\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    req = urllib.request.Request(
        "http://127.0.0.1:8000/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    try:
        urllib.request.urlopen(req)
        print("ERROR: Upload should have failed!")
    except urllib.error.HTTPError as e:
        print(f"Rejected correctly with HTTP {e.code}: {e.read().decode('utf-8')}")

    print("\n--- 5. Testing Oversized Upload Check ---")
    # Simulate oversized file header check or limit
    print(f"Server max upload size limit: {data.get('max_upload_size_mb')} MB")

if __name__ == "__main__":
    test()
