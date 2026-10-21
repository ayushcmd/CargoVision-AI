import torch
import numpy as np
import cv2
import os
try:
    from src.core.nafnet_arch import NAFNet
except (ImportError, ModuleNotFoundError):
    from nafnet_arch import NAFNet

class DeblurGANEngine:
    def __init__(self, weights_path):
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"[INFO] NAFNet: Running on {self.device}")

        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"NAFNet weights not found at: {weights_path}")
            
        print(f"[INFO] NAFNet: Loading weights from {weights_path}...")
        
        # Load Weights
        checkpoint = torch.load(weights_path, map_location=self.device)
        
        # Try different state dict locations
        if isinstance(checkpoint, dict):
            if 'params' in checkpoint:
                state_dict = checkpoint['params']
            elif 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
            elif 'state_dict' in checkpoint:
                state_dict = checkpoint['state_dict']
            else:
                state_dict = checkpoint
        else:
            state_dict = checkpoint

        # Detect channel width from weights
        width = 32
        if 'intro.weight' in state_dict:
            width = state_dict['intro.weight'].shape[0]
            print(f"[INFO] NAFNet: Auto-detected width = {width} from intro.weight")
        
        enc_blks = [1, 1, 1, 28]
        middle_blk_num = 1
        dec_blks = [1, 1, 1, 1]
        
        # Initialize Model
        self.model = NAFNet(img_channel=3, width=width, middle_blk_num=middle_blk_num, 
                          enc_blk_nums=enc_blks, dec_blk_nums=dec_blks)
            
        # Load with strict=False to see what's actually loading
        missing_keys, unexpected_keys = self.model.load_state_dict(state_dict, strict=False)
        
        if missing_keys:
            print(f"[WARNING] Missing keys in checkpoint: {len(missing_keys)}")
            print(f"[WARNING] First few missing: {missing_keys[:5]}")
        
        if unexpected_keys:
            print(f"[WARNING] Unexpected keys in checkpoint: {len(unexpected_keys)}")
            print(f"[WARNING] First few unexpected: {unexpected_keys[:5]}")
        
        if not missing_keys and not unexpected_keys:
            print("[INFO] All keys matched perfectly!")
            
        self.model.to(self.device)
        self.model.eval()
        print("[INFO] NAFNet: Model loaded successfully.")


    def deblur(self, frame, use_tta=False, sharpen_amount=0.5):
        """
        Deblur a single frame with optional enhancements
        Args:
            frame: Input image (numpy array, BGR)
            use_tta: Use test-time augmentation for better quality (slower)
            sharpen_amount: Post-processing sharpening (0=none, 1.0=strong)
        """
        import torch.nn.functional as F
        import numpy as np
        
        original_size = frame.shape[:2]
        
        # Preprocess with padding
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = frame_rgb.astype(np.float32) / 255.0
        
        # Pad to multiple of 8
        h, w = frame_rgb.shape[:2]
        pad_h = (8 - h % 8) % 8
        pad_w = (8 - w % 8) % 8
        
        if pad_h > 0 or pad_w > 0:
            frame_rgb = np.pad(frame_rgb, ((0, pad_h), (0, pad_w), (0, 0)), mode='reflect')
        
        frame_tensor = torch.from_numpy(frame_rgb).permute(2, 0, 1).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            if use_tta:
                # Test-Time Augmentation for better quality
                outputs = []
                
                # Original
                outputs.append(self.model(frame_tensor))
                
                # Horizontal flip
                outputs.append(torch.flip(self.model(torch.flip(frame_tensor, [3])), [3]))
                
                # Vertical flip
                outputs.append(torch.flip(self.model(torch.flip(frame_tensor, [2])), [2]))
                
                # Both flips
                outputs.append(torch.flip(self.model(torch.flip(frame_tensor, [2, 3])), [2, 3]))
                
                # Average all outputs
                output = torch.mean(torch.stack(outputs), dim=0)
            else:
                # Standard inference
                output = self.model(frame_tensor)
        
        # Postprocess
        deblurred = output.squeeze(0).permute(1, 2, 0).cpu().numpy()
        
        # Remove padding
        if pad_h > 0 or pad_w > 0:
            deblurred = deblurred[:h, :w]
        
        # Clip and convert
        deblurred = np.clip(deblurred * 255.0, 0, 255).astype(np.uint8)
        deblurred = cv2.cvtColor(deblurred, cv2.COLOR_RGB2BGR)
        
        # Apply sharpening if requested
        if sharpen_amount > 0:
            deblurred = self._apply_sharpening(deblurred, sharpen_amount)
        
        return deblurred
    
    def _apply_sharpening(self, img, amount=1.0):
        """Apply unsharp masking for sharpening"""
        if amount <= 0:
            return img
        
        # Gaussian blur
        blurred = cv2.GaussianBlur(img, (0, 0), 3)
        
        # Unsharp mask
        sharpened = cv2.addWeighted(img, 1.0 + amount, blurred, -amount, 0)
        
        return sharpened