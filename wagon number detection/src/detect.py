import cv2
import sys
import os

# Add the parent directory to sys.path to allow importing 'wnd'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wnd import WagonNumberDetection

videoPath = "vids/4.MP4"
output_path = "results/output_4.mp4"

# Ensure results directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

vid = cv2.VideoCapture(videoPath)

# --- Setup Video Writer ---
frame_width = int(vid.get(3))
frame_height = int(vid.get(4))
fps = int(vid.get(cv2.CAP_PROP_FPS))
fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
# --------------------------

previousWagonNumber = ""
currentWagonNumber = ""

print(f"Processing video... Saving to {output_path}")

while True:
    ret, frame = vid.read()

    if not ret:
        print("End of video.")
        break
    
    wagonNumber, outputFrame = WagonNumberDetection.DetectWagonNumber(frame)

    currentWagonNumber = wagonNumber
    if currentWagonNumber == "" or previousWagonNumber == currentWagonNumber:
        print("no wagon number")
    else:
        cv2.putText(frame, wagonNumber, (230, 380), cv2.FONT_HERSHEY_DUPLEX, 1.8, (255,255,255) , 1, cv2.LINE_AA)
        
    # Write the frame to the file
    out.write(frame)

    cv2.imshow("frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

vid.release()
out.release()
cv2.destroyAllWindows()
print("Done.")
