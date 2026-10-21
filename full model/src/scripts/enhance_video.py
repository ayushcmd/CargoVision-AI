import cv2
import argparse
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.core.enhancer import LowLightEnhancer

def enhance_video(video_path: str, weights_path: str, show_display: bool):
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    # Initialize enhancer
    # Check if CUDA is available
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    enhancer = LowLightEnhancer(weights_path=weights_path, device=device)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    frame_count = 0
    start_time = time.time()

    print(f"Enhancing video: {video_path}")
    print("-" * 30)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        
        # Resize for faster processing if needed (optional)
        # frame = cv2.resize(frame, (640, 360))

        enhanced_frame = enhancer.enhance_frame(frame)
        
        # Stack images side-by-side
        # Resize to same height if needed (usually they are same)
        combined = cv2.hconcat([frame, enhanced_frame])

        if show_display:
            # Resize for display to fit screen
            display_h = 400
            scale = display_h / combined.shape[0]
            display_w = int(combined.shape[1] * scale)
            display_frame = cv2.resize(combined, (display_w, display_h))
            
            cv2.putText(display_frame, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(display_frame, "Enhanced", (int(display_w/2) + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow('Low Light Enhancement', display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")

    end_time = time.time()
    fps = frame_count / (end_time - start_time)
    
    cap.release()
    cv2.destroyAllWindows()
    
    print("-" * 30)
    print(f"Total Frames: {frame_count}")
    print(f"Average FPS: {fps:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhance low-light video.")
    parser.add_argument("--video_path", type=str, required=True, help="Path to the input video file.")
    parser.add_argument("--weights_path", type=str, default="weights/Zero_DCE.pth", help="Path to model weights.")
    parser.add_argument("--no-display", action="store_true", help="Run without displaying the video window.")
    
    args = parser.parse_args()
    
    enhance_video(args.video_path, args.weights_path, not args.no_display)
