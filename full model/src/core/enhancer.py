import torch
import torch.nn as nn
import numpy as np
import cv2
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# --------------------------------------------------------------------------------
# ZERO-DCE (Legacy - Commented Out)
# --------------------------------------------------------------------------------
# from src.core.zero_dce import enhance_net_nopool

# --------------------------------------------------------------------------------
# SCI (Self-Calibrated Illumination) Integration
# --------------------------------------------------------------------------------
class EnhanceNetwork(nn.Module):
    def __init__(self, layers=3, channels=3):
        super(EnhanceNetwork, self).__init__()

        kernel_size = 3
        dilation = 1
        padding = int((kernel_size - 1) / 2) * dilation

        # SCI uses a specific block structure
        self.in_conv = nn.Conv2d(in_channels=channels, out_channels=channels, kernel_size=kernel_size, padding=padding)
        self.conv = nn.Conv2d(in_channels=channels, out_channels=channels, kernel_size=kernel_size, padding=padding)
        self.relu = nn.ReLU()

    def forward(self, input):
        # The official logic has a specific residual connection
        x = self.in_conv(input)
        x = self.relu(x)
        x = self.conv(x)

        # PREDICT ILLUMINATION MAP
        illumination = torch.sigmoid(x) # Crucial! Sigmoid forces 0-1 range

        # APPLY RETINEX (Input / Illumination)
        # Add epsilon to prevent divide-by-zero (Red Screen fix)
        output = input / (illumination + 0.0001) 
        
        # Clamp to avoid weird artifacts
        output = torch.clamp(output, 0, 1)

        return output

class LowLightEnhancer:
    def __init__(self, weights_path=None, device='cpu'):
        self.device = torch.device(device)
        # Initialize the Correct Architecture
        self.model = EnhanceNetwork(layers=3, channels=3).to(self.device)
        
        # WEIGHT LOADING LOGIC
        if weights_path is None:
             # Try to find weights automatically
             base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../full model/SCI'))
             weights_path = os.path.join(base_dir, 'medium.pt') # Recommend 'medium.pt' over 'difficult.pt'

        if weights_path and os.path.exists(weights_path):
            print(f"[LowLightEnhancer] Loading SCI weights from {weights_path}")
            try:
                # strict=False allows partial loading if your pytorch version differs slightly
                self.model.load_state_dict(torch.load(weights_path, map_location=self.device), strict=False)
            except Exception as e:
                print(f"[CRITICAL ERROR] Weight Mismatch: {e}")
                print("Using Random Weights (expect bad results!)")

        else:
            print(f"[LowLightEnhancer] Warning: Weights file not found. Using Random Weights.")

        self.model.eval()

    def enhance_frame(self, frame: np.ndarray) -> np.ndarray:
        if frame is None: return None
        
        # 1. BGR -> RGB & Normalize
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).to(self.device)

        # 2. Inference
        with torch.no_grad():
            enhanced_tensor = self.model(img_tensor)

        # 3. Post-Process
        result = enhanced_tensor.squeeze().permute(1, 2, 0).cpu().numpy()
        result = np.clip(result * 255.0, 0, 255).astype(np.uint8)

        # 4. RGB -> BGR
        return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)