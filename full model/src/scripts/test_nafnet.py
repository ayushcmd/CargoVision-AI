import argparse
import cv2
import os
import sys
import torch
import numpy as np
from pathlib import Path

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
    
    # Initialize NAFNet model - CORRECTED to match finetuned checkpoint
    model = NAFNet(
        img_channel=3,
        width=64,
        middle_blk_num=1,              # Changed from 12 to 1
        enc_blk_nums=[1, 1, 1, 28],    # Changed from [2, 2, 4, 8]
        dec_blk_nums=[1, 1, 1, 1]      # Changed from [2, 2, 2, 2]
    ).to(device)
    
    # Load weights
    checkpoint = torch.load(model_path, map_location=device)
    
    # Debug: print checkpoint structure
    print(f"[DEBUG] Checkpoint keys: {list(checkpoint.keys())[:5]}")
    
    # Handle different checkpoint formats
    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    elif 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    else:
        state_dict = checkpoint
    
    # Print first few keys to understand structure
    if isinstance(state_dict, dict):
        print(f"[DEBUG] State dict keys sample: {list(state_dict.keys())[:5]}")
    
    # Load with strict=False to see what loads
    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
    
    if missing_keys:
        print(f"[WARNING] Missing keys: {len(missing_keys)} (showing first 10)")
        for key in missing_keys[:10]:
            print(f"  - {key}")
    
    if unexpected_keys:
        print(f"[WARNING] Unexpected keys: {len(unexpected_keys)} (showing first 10)")
        for key in unexpected_keys[:10]:
            print(f"  - {key}")
    
    model.eval()
    print(f"[INFO] Model loaded successfully")
    return model, device

def preprocess_image(img, pad_to_multiple=8):
    """Convert image to tensor with padding for better processing"""
    h, w = img.shape[:2]
    
    # Pad to multiple of pad_to_multiple for better processing
    new_h = ((h + pad_to_multiple - 1) // pad_to_multiple) * pad_to_multiple
    new_w = ((w + pad_to_multiple - 1) // pad_to_multiple) * pad_to_multiple
    
    pad_h = new_h - h
    pad_w = new_w - w
    
    # Pad image
    img_padded = cv2.copyMakeBorder(img, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
    
    # Normalize to [0, 1]
    img_padded = img_padded.astype(np.float32) / 255.0
    # Convert BGR to RGB
    img_padded = cv2.cvtColor(img_padded, cv2.COLOR_BGR2RGB)
    # HWC to CHW
    img_padded = np.transpose(img_padded, (2, 0, 1))
    # Add batch dimension
    img_padded = np.expand_dims(img_padded, 0)
    
    return torch.from_numpy(img_padded), (h, w)

def postprocess_image(tensor, original_size):
    """Convert tensor back to image and crop to original size"""
    h, w = original_size
    
    # Remove batch dimension
    img = tensor.squeeze(0)
    # CHW to HWC
    img = img.permute(1, 2, 0)
    # Convert to numpy
    img = img.cpu().numpy()
    
    # Crop to original size
    img = img[:h, :w, :]
    
    # Denormalize to [0, 255]
    img = np.clip(img * 255.0, 0, 255).astype(np.uint8)
    # Convert RGB to BGR
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img

def apply_sharpening(img, amount=1.0):
    """Apply unsharp masking for enhanced sharpness"""
    if amount <= 0:
        return img
    
    # Create Gaussian blur
    blurred = cv2.GaussianBlur(img, (0, 0), 3)
    # Create sharpened image
    sharpened = cv2.addWeighted(img, 1.0 + amount, blurred, -amount, 0)
    return sharpened

def test_time_augmentation(model, input_tensor, device):
    """Apply test-time augmentation for better results"""
    outputs = []
    
    # Original
    with torch.no_grad():
        out = model(input_tensor)
        outputs.append(out)
    
    # Horizontal flip
    input_flip = torch.flip(input_tensor, [3])
    with torch.no_grad():
        out_flip = model(input_flip)
        out_flip = torch.flip(out_flip, [3])
        outputs.append(out_flip)
    
    # Vertical flip
    input_vflip = torch.flip(input_tensor, [2])
    with torch.no_grad():
        out_vflip = model(input_vflip)
        out_vflip = torch.flip(out_vflip, [2])
        outputs.append(out_vflip)
    
    # Both flips
    input_both = torch.flip(input_tensor, [2, 3])
    with torch.no_grad():
        out_both = model(input_both)
        out_both = torch.flip(out_both, [2, 3])
        outputs.append(out_both)
    
    # Average all outputs
    output = torch.stack(outputs).mean(dim=0)
    return output

def main():
    parser = argparse.ArgumentParser(description='Test NAFNet deblurring model')
    parser.add_argument('--input', '-i', required=True, help='Input image path')
    parser.add_argument('--output', '-o', required=True, help='Output image path')
    parser.add_argument('--model', '-m', 
                       default='finetuned_nafnet/nafnet_wagon_finetuned.pth',
                       help='Model weights path (relative to project root)')
    parser.add_argument('--tta', action='store_true', 
                       help='Use test-time augmentation (slower but better quality)')
    parser.add_argument('--sharpen', type=float, default=0.5,
                       help='Sharpening amount (0=none, 0.5=mild, 1.0=strong)')
    parser.add_argument('--save-comparison', action='store_true',
                       help='Save side-by-side comparison image')
    
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
        print(f"[ERROR] Input image not found: {args.input}")
        return
    
    if not os.path.exists(args.model):
        print(f"[ERROR] Model weights not found: {args.model}")
        return
    
    # Load image
    print(f"[INFO] Loading image: {args.input}")
    img = cv2.imread(args.input)
    
    if img is None:
        print(f"[ERROR] Failed to load image")
        return
    
    print(f"[INFO] Image size: {img.shape[:2]}")
    
    # Load model
    print(f"[INFO] Loading NAFNet model: {args.model}")
    try:
        model, device = load_model(args.model)
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Preprocess
    print(f"[INFO] Processing...")
    input_tensor, original_size = preprocess_image(img)
    input_tensor = input_tensor.to(device)
    
    # Inference
    if args.tta:
        print(f"[INFO] Using test-time augmentation (4x slower but better quality)...")
        output_tensor = test_time_augmentation(model, input_tensor, device)
    else:
        with torch.no_grad():
            output_tensor = model(input_tensor)
    
    # Postprocess
    deblurred = postprocess_image(output_tensor, original_size)
    
    # Apply sharpening if requested
    if args.sharpen > 0:
        print(f"[INFO] Applying sharpening (amount={args.sharpen})...")
        deblurred = apply_sharpening(deblurred, args.sharpen)
    
    # Save output
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    cv2.imwrite(args.output, deblurred)
    
    print(f"[SUCCESS] Deblurred image saved to: {args.output}")
    print(f"[INFO] Output size: {deblurred.shape[:2]}")
    
    # Save comparison if requested
    if args.save_comparison:
        comparison_path = args.output.replace('.jpg', '_comparison.jpg').replace('.png', '_comparison.png')
        # Resize images to same height if needed
        h1, h2 = img.shape[0], deblurred.shape[0]
        if h1 != h2:
            scale = h1 / h2
            deblurred_resized = cv2.resize(deblurred, None, fx=scale, fy=scale)
        else:
            deblurred_resized = deblurred
        
        comparison = np.hstack([img, deblurred_resized])
        cv2.imwrite(comparison_path, comparison)
        print(f"[INFO] Comparison saved to: {comparison_path}")

if __name__ == "__main__":
    main()


# command to test the code 
# python src/scripts/test_nafnet.py -i "wagon_number_dataset/images/wagon_OCR_video_1_f000070_id3.jpg" -o "output.jpg" -m "finetuned_nafnet/nafnet_wagon_finetuned.pth" --tta --sharpen 0.8 --save-comparison