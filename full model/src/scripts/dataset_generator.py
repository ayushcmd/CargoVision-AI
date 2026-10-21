import cv2
import os
import argparse
from ultralytics import YOLO

# -------------------------------------------------
# Extract wagon crops for Model B finetuning
# -------------------------------------------------

def extract_wagon_crops(
    video_path,
    model_a_path,
    output_dir,
    frame_stride=5,      # take 1 frame every N frames
    min_area_ratio=0.03,
    max_area_ratio=0.40
):
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "labels"), exist_ok=True)

    print(f"[INFO] Loading Model A: {model_a_path}")
    model_a = YOLO(model_a_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Could not open video")

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    frame_idx = 0
    saved = 0

    video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    image_area = video_w * video_h

    print("[INFO] Starting frame extraction...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # Sample frames
        if frame_idx % frame_stride != 0:
            continue

        results = model_a.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )

        if not results or results[0].boxes.id is None:
            continue

        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.cpu().numpy()
        clss = results[0].boxes.cls.cpu().numpy()

        for box, track_id, cls in zip(boxes, ids, clss):
            # Wagon classes only (adjust if needed)
            if int(cls) not in [0, 6]:
                continue

            x1, y1, x2, y2 = map(int, box)
            if x2 <= x1 or y2 <= y1:
                continue

            area_ratio = ((x2 - x1) * (y2 - y1)) / image_area
            if not (min_area_ratio < area_ratio < max_area_ratio):
                continue

            wagon_crop = frame[y1:y2, x1:x2]
            if wagon_crop.size == 0:
                continue

            fname = f"wagon_{video_name}_f{frame_idx:06d}_id{int(track_id)}.jpg"
            out_path = os.path.join(output_dir, "images", fname)

            cv2.imwrite(out_path, wagon_crop)
            saved += 1

        if frame_idx % 200 == 0:
            print(f"[INFO] Processed {frame_idx} frames | Saved {saved} crops")

    cap.release()
    print("-" * 50)
    print(f"[DONE] Total wagon crops saved: {saved}")
    print(f"[DONE] Output directory: {output_dir}")
    print("-" * 50)


# -------------------------------------------------
# CLI
# -------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_path", required=True)
    parser.add_argument(
        "--model_a",
        default="../../railway_hackathon_take6/merged_model_v6_generalized/weights/best.pt"
    )
    parser.add_argument(
        "--output_dir",
        default="wagon_number_dataset"
    )
    parser.add_argument(
        "--frame_stride",
        type=int,
        default=5
    )

    args = parser.parse_args()

    extract_wagon_crops(
        video_path=args.video_path,
        model_a_path=args.model_a,
        output_dir=args.output_dir,
        frame_stride=args.frame_stride
    )
