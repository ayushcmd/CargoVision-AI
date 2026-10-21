import cv2
import argparse
from ultralytics import YOLO
import os
import sys

def detect_video(video_path: str, weights_path: str, output_path: str = None):
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return
    
    if not os.path.exists(weights_path):
        print(f"Error: Weights file not found at {weights_path}")
        print("Please check the path. It should be usually in 'railway_hackathon/wagon_counter_v1/weights/best.pt'")
        return

    print(f"Loading model from {weights_path}...")
    model = YOLO(weights_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    out = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Processing video: {video_path}")
    print("Press 'q' to quit early.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run inference
        results = model(frame, verbose=False)
        
        # Plot results on the frame
        annotated_frame = results[0].plot()

        if out:
            out.write(annotated_frame)

        # cv2.imshow('Wagon Detection', annotated_frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
        if out is None:
            pass

    cap.release()
    if out:
        out.release()
    print("Processing complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run YOLOv8 detection on a video.")
    parser.add_argument("--video_path", type=str, required=True, help="Path to the input video file.")
    # Default to the path where training likely saved it, assuming run from 'full model' dir
    parser.add_argument("--weights_path", type=str, default="railway_hackathon/wagon_counter_v1/weights/best.pt", help="Path to trained weights.")
    parser.add_argument("--output_path", type=str, default=None, help="Path to save output video (optional).")
    
    args = parser.parse_args()
    
    detect_video(args.video_path, args.weights_path, args.output_path)
