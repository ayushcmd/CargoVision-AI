import argparse
import cv2
import os
import sys
import torch
import numpy as np
from pathlib import Path
from tqdm import tqdm

# Add project paths
script_dir = Path(__file__).parent
src_dir = script_dir.parent
project_root = src_dir.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

# Import NAFNet from core directory
from core.nafnet_arch import NAFNet


def load_model(model_path, device='cuda' if torch.cuda.is_available() else 'cpu'):
    """Load NAFNet model from checkpoint"""
    print(f"[INFO] Using device: {device}")
    
    # Initialize NAFNet model - matches finetuned checkpoint
    model = NAFNet(
        img_channel=3,
        width=64,
        middle_blk_num=1,
        enc_blk_nums=[1, 1, 1, 28],
        dec_blk_nums=[1, 1, 1, 1]
    ).to(device)
    
    # Load weights
    checkpoint = torch.load(model_path, map_location=device)
    
    # Handle different checkpoint formats
    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    elif 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    else:
        state_dict = checkpoint
    
    model.load_state_dict(state_dict, strict=False)
    model.eval()
    print(f"[INFO] Model loaded successfully")
    return model, device


def preprocess_frame(frame, pad_to_multiple=8):
    """Convert frame to tensor with padding"""
    h, w = frame.shape[:2]
    
    # Pad to multiple
    new_h = ((h + pad_to_multiple - 1) // pad_to_multiple) * pad_to_multiple
    new_w = ((w + pad_to_multiple - 1) // pad_to_multiple) * pad_to_multiple
    
    pad_h = new_h - h
    pad_w = new_w - w
    
    # Pad frame
    frame_padded = cv2.copyMakeBorder(frame, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
    
    # Normalize to [0, 1]
    frame_padded = frame_padded.astype(np.float32) / 255.0
    # Convert BGR to RGB
    frame_padded = cv2.cvtColor(frame_padded, cv2.COLOR_BGR2RGB)
    # HWC to CHW
    frame_padded = np.transpose(frame_padded, (2, 0, 1))
    # Add batch dimension
    frame_padded = np.expand_dims(frame_padded, 0)
    
    return torch.from_numpy(frame_padded), (h, w)


def postprocess_frame(tensor, original_size):
    """Convert tensor back to frame and crop to original size"""
    h, w = original_size
    
    # Remove batch dimension
    frame = tensor.squeeze(0)
    # CHW to HWC
    frame = frame.permute(1, 2, 0)
    # Convert to numpy
    frame = frame.cpu().numpy()
    
    # Crop to original size
    frame = frame[:h, :w, :]
    
    # Denormalize to [0, 255]
    frame = np.clip(frame * 255.0, 0, 255).astype(np.uint8)
    # Convert RGB to BGR
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return frame


def apply_sharpening(frame, amount=1.0):
    """Apply unsharp masking for enhanced sharpness"""
    if amount <= 0:
        return frame
    
    blurred = cv2.GaussianBlur(frame, (0, 0), 3)
    sharpened = cv2.addWeighted(frame, 1.0 + amount, blurred, -amount, 0)
    return sharpened


def test_time_augmentation(model, input_tensor, device):
    """Apply test-time augmentation for better results"""
    outputs = []
    
    with torch.no_grad():
        # Original
        outputs.append(model(input_tensor))
        
        # Horizontal flip
        input_flip = torch.flip(input_tensor, [3])
        out_flip = model(input_flip)
        outputs.append(torch.flip(out_flip, [3]))
        
        # Vertical flip
        input_vflip = torch.flip(input_tensor, [2])
        out_vflip = model(input_vflip)
        outputs.append(torch.flip(out_vflip, [2]))
        
        # Both flips
        input_both = torch.flip(input_tensor, [2, 3])
        out_both = model(input_both)
        outputs.append(torch.flip(out_both, [2, 3]))
    
    # Average all outputs
    output = torch.stack(outputs).mean(dim=0)
    return output


def process_video(input_path, output_path, model, device, use_tta=False, sharpen=0.5, 
                  save_comparison=False, skip_frames=0, max_frames=None):
    """Process entire video through NAFNet"""
    
    # Open input video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {input_path}")
        return False
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"[INFO] Video properties:")
    print(f"       Resolution: {width}x{height}")
    print(f"       FPS: {fps}")
    print(f"       Total frames: {total_frames}")
    
    # Limit frames if specified
    if max_frames:
        total_frames = min(total_frames, max_frames + skip_frames)
    
    # Setup output video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    if save_comparison:
        # Side-by-side comparison (double width)
        out = cv2.VideoWriter(output_path, fourcc, fps, (width * 2, height))
    else:
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        print(f"[ERROR] Cannot create output video: {output_path}")
        cap.release()
        return False
    
    # Skip initial frames if specified
    if skip_frames > 0:
        print(f"[INFO] Skipping first {skip_frames} frames...")
        for _ in range(skip_frames):
            cap.read()
    
    # Process frames
    frame_count = 0
    processed_frames = total_frames - skip_frames
    
    print(f"[INFO] Processing {processed_frames} frames...")
    print(f"[INFO] TTA: {'Enabled (4x slower)' if use_tta else 'Disabled'}")
    print(f"[INFO] Sharpening: {sharpen}")
    
    pbar = tqdm(total=processed_frames, desc="Deblurring", unit="frame")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if max_frames and frame_count >= max_frames:
            break
        
        # Preprocess
        input_tensor, original_size = preprocess_frame(frame)
        input_tensor = input_tensor.to(device)
        
        # Inference
        if use_tta:
            output_tensor = test_time_augmentation(model, input_tensor, device)
        else:
            with torch.no_grad():
                output_tensor = model(input_tensor)
        
        # Postprocess
        deblurred = postprocess_frame(output_tensor, original_size)
        
        # Apply sharpening
        if sharpen > 0:
            deblurred = apply_sharpening(deblurred, sharpen)
        
        # Write frame
        if save_comparison:
            comparison = np.hstack([frame, deblurred])
            out.write(comparison)
        else:
            out.write(deblurred)
        
        frame_count += 1
        pbar.update(1)
    
    pbar.close()
    
    # Cleanup
    cap.release()
    out.release()
    
    print(f"[SUCCESS] Processed {frame_count} frames")
    print(f"[SUCCESS] Output saved to: {output_path}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Test NAFNet deblurring on video')
    parser.add_argument('--input', '-i', required=True, help='Input video path')
    parser.add_argument('--output', '-o', required=True, help='Output video path')
    parser.add_argument('--model', '-m', 
                       default='finetuned_nafnet/nafnet_wagon_finetuned.pth',
                       help='Model weights path (relative to project root)')
    parser.add_argument('--tta', action='store_true', 
                       help='Use test-time augmentation (4x slower but better quality)')
    parser.add_argument('--sharpen', type=float, default=0.5,
                       help='Sharpening amount (0=none, 0.5=mild, 1.0=strong)')
    parser.add_argument('--save-comparison', action='store_true',
                       help='Save side-by-side comparison video (original | deblurred)')
    parser.add_argument('--skip-frames', type=int, default=0,
                       help='Skip first N frames')
    parser.add_argument('--max-frames', type=int, default=None,
                       help='Process only first N frames (after skipping)')
    parser.add_argument('--resize', type=float, default=None,
                       help='Resize factor (e.g., 0.5 for half resolution, faster processing)')
    
    args = parser.parse_args()
    
    # Convert paths to absolute if needed
    if not os.path.isabs(args.input):
        args.input = os.path.join(project_root, args.input)
    if not os.path.isabs(args.output):
        args.output = os.path.join(project_root, args.output)
    if not os.path.isabs(args.model):
        args.model = os.path.join(project_root, args.model)
    
    # Validate input
    if not os.path.exists(args.input):
        print(f"[ERROR] Input video not found: {args.input}")
        return
    
    if not os.path.exists(args.model):
        print(f"[ERROR] Model weights not found: {args.model}")
        return
    
    # Create output directory if needed
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Load model
    print(f"[INFO] Loading NAFNet model: {args.model}")
    try:
        model, device = load_model(args.model)
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Process video
    success = process_video(
        args.input, 
        args.output, 
        model, 
        device,
        use_tta=args.tta,
        sharpen=args.sharpen,
        save_comparison=args.save_comparison,
        skip_frames=args.skip_frames,
        max_frames=args.max_frames
    )
    
    if success:
        print(f"\n[DONE] Video deblurring complete!")
        print(f"[INFO] Input:  {args.input}")
        print(f"[INFO] Output: {args.output}")


if __name__ == "__main__":
    main()