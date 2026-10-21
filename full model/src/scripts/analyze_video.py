import cv2
import argparse
import sys
import os

# Add the project root to the python path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.core.blur_metric import calculate_blur_score, is_frame_sharp

def analyze_video(video_path: str, threshold: float, show_display: bool):
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    frame_count = 0
    kept_frames = 0
    
    print(f"Processing video: {video_path}")
    print(f"Blur Threshold: {threshold}")
    print("-" * 30)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        score = calculate_blur_score(frame)
        sharp = is_frame_sharp(score, threshold)
        
        status = "SHARP" if sharp else "BLURRY"
        color = (0, 255, 0) if sharp else (0, 0, 255) # Green for sharp, Red for blurry
        
        if sharp:
            kept_frames += 1

        print(f"Frame {frame_count}: Score: {score:.2f} - {status}")

        if show_display:
            # Resize for better viewing if needed
            display_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5) 
            
            # Put text on the frame
            cv2.putText(display_frame, f"Score: {score:.2f} ({status})", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            cv2.imshow('Frame Analysis', display_frame)
            
            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    
    print("-" * 30)
    print(f"Total Frames: {frame_count}")
    print(f"Kept Frames: {kept_frames}")
    print(f"Discarded Frames: {frame_count - kept_frames}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze video for blur.")
    parser.add_argument("--video_path", type=str, required=True, help="Path to the input video file.")
    parser.add_argument("--threshold", type=float, default=100.0, help="Blur threshold (default: 100.0). Higher means stricter.")
    parser.add_argument("--no-display", action="store_true", help="Run without displaying the video window.")
    
    args = parser.parse_args()
    
    analyze_video(args.video_path, args.threshold, not args.no_display)
