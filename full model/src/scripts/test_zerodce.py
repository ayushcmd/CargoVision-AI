import cv2
import argparse
import os
import sys
import time

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.core.enhancer import LowLightEnhancer

def process_video(video_path, output_path, weights_path=None):
    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        return

    import torch
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Initializing Enhancer with weights: {weights_path or 'Default (SCI difficult)'} on {device}")
    
    if device == 'cpu':
        print("[WARNING] CUDA not available. Running on CPU (will be slower).")

    enhancer = LowLightEnhancer(weights_path=weights_path, device=device)

    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Processing {video_path} ({width}x{height} @ {fps}fps)")
    print(f"Output will be saved to {output_path}")

    # Video Writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_cnt = 0
    start_time = time.time()

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            frame_cnt += 1
            
            # Enhancer
            t0 = time.time()
            enhanced = enhancer.enhance_frame(frame)
            t1 = time.time()
            
            # Calculate FPS
            proc_fps = 1.0 / (t1 - t0)
            
            # Side-by-Side Visualization (Optional debug view)
            # vis = np.hstack((frame, enhanced))
            # cv2.imshow('Original vs Enhanced', cv2.resize(vis, (0,0), fx=0.5, fy=0.5))
            # if cv2.waitKey(1) & 0xFF == ord('q'): break
            
            out.write(enhanced)
            
            if frame_cnt % 10 == 0:
                print(f"Frame {frame_cnt}/{total_frames} | Speed: {proc_fps:.1f} FPS")

    except KeyboardInterrupt:
        print("Interrupted by user.")

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    total_time = time.time() - start_time
    print(f"Done! Processed {frame_cnt} frames in {total_time:.1f}s ({frame_cnt/total_time:.1f} FPS avg)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path", help="Path to input video")
    parser.add_argument("--output", default="output_enhanced.mp4", help="Path to output video")
    parser.add_argument("--weights", help="Path to model weights (optional)")
    
    args = parser.parse_args()
    process_video(args.video_path, args.output, args.weights)
