# from paddleocr import PaddleOCR
# import cv2
# import numpy as np
# import logging

# # Suppress PaddleOCR logs
# logging.getLogger("ppocr").setLevel(logging.ERROR)

# class WagonOCR:
#     def __init__(self):
#         # use_angle_cls=True: Rotates text if the wagon is tilted (very common)
#         # lang='en': We only need English numbers/letters
#         # show_log=False: Keeps your terminal clean
#         print("Initializing PaddleOCR...")
#         self.ocr = PaddleOCR(use_angle_cls=True, lang='en', ocr_version='PP-OCRv3')

#     def process_wagon(self, wagon_crop_image):
#         """
#         Input: The cropped image of ONE wagon (from YOLO).
#         Output: The detected Wagon Number string.
#         """
#         if wagon_crop_image is None or wagon_crop_image.size == 0:
#             return None

#         # --- INSERT DEBLURRING HERE LATER ---
#         # wagon_crop_image = deblur_model(wagon_crop_image)
#         # ------------------------------------

#         # Run OCR
#         # cls=True runs the angle classifier
#         try:
#             result = self.ocr.ocr(wagon_crop_image)
#         except Exception as e:
#             print(f"OCR Error: {e}")
#             return None

#         # Paddle returns a complex list. Let's parse the best result.
#         detected_text = []
#         if result and result[0]:
#             for line in result[0]:
#                 text = None
#                 confidence = 1.0  # default if not provided

#                 if isinstance(line[1], (list, tuple)):
#                     text = line[1][0]
#                     if len(line[1]) > 1 and isinstance(line[1][1], (float, int)):
#                         confidence = float(line[1][1])
#                 elif isinstance(line[1], str):
#                     text = line[1]
                
#                 # Filter noise: Wagon numbers usually have 5+ digits
#                 # Relaxed: > 0.4 conf, > 0 chars (Show anything)
#                 print(f"      [Paddle Raw] Text: '{text}' | Conf: {confidence:.2f}")
#                 if confidence > 0.4 and len(text) >= 1:
#                     detected_text.append(text)

#         if not detected_text:
#              print("      [OCR] No valid text found after filtering.")
#              return None

#         # Return the most likely text (or join them if split across lines)
#         full_text = " ".join(detected_text)
#         print(f"      [Final Selection] {full_text}")
#         return full_text


# pip install easyocr

import easyocr
import torch
import cv2
import numpy as np

try:
    from src.core.indian_railways import IndianWagonParser
except (ImportError, ModuleNotFoundError):
    try:
        from indian_railways import IndianWagonParser
    except (ImportError, ModuleNotFoundError):
        IndianWagonParser = None

class WagonOCR:
    def __init__(self):
        print("Initializing EasyOCR...")
        self.reader = self._init_reader()

    def _init_reader(self):
        """Force CPU for OCR to avoid VRAM contention with main pipeline."""
        print("Initializing EasyOCR on CPU (Forced to save VRAM)...")
        return easyocr.Reader(['en'], gpu=False)

    def preprocess_crop(self, crop):
        """Enhances contrast and resolution for railway text reading."""
        if crop is None or crop.size == 0:
            return crop

        # Aspect-ratio preserving upscale if character height is too low
        h, w = crop.shape[:2]
        target_h = 140
        if h < target_h:
            scale = target_h / float(h)
            crop = cv2.resize(crop, (int(w * scale), target_h), interpolation=cv2.INTER_LANCZOS4)

        # Contrast Limited Adaptive Histogram Equalization on Luminance channel
        lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l_ch)
        enhanced = cv2.merge((cl, a_ch, b_ch))
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    def normalize_railway_text(self, raw_str):
        """Maps common OCR visual confusions specifically for Indian Railways numeric codes."""
        char_map = {
            'I': '1', 'i': '1', 'l': '1', '|': '1', '/': '1', '\\': '1',
            'O': '0', 'o': '0', 'D': '0', 'Q': '0',
            'B': '8',
            'Z': '2', 'z': '2',
            'S': '5', 's': '5',
            'g': '9', 'q': '9',
            'e': '8'
        }
        clean = []
        for ch in raw_str:
            if ch.isdigit():
                clean.append(ch)
            elif ch in char_map:
                clean.append(char_map[ch])
        return ''.join(clean)

    def process_wagon(self, wagon_crop_image):
        if wagon_crop_image is None or wagon_crop_image.size == 0:
            return None

        # Preprocess crop
        prep_img = self.preprocess_crop(wagon_crop_image)

        try:
            results = self.reader.readtext(prep_img)
        except Exception as e:
            print(f"OCR Error: {e}")
            return None

        if not results:
            # Fallback to raw crop if preprocessed yielded nothing
            try:
                results = self.reader.readtext(wagon_crop_image)
            except Exception:
                return None

        # Sort left-to-right based on bounding box
        results_sorted = sorted(results, key=lambda r: r[0][0][0])
        detected_tokens = []

        for (bbox, text, confidence) in results_sorted:
            print(f"      [EasyOCR Raw] Text: '{text}' | Conf: {confidence:.2f}")
            if confidence > 0.15 and len(text.strip()) >= 1:
                norm_text = self.normalize_railway_text(text)
                if norm_text:
                    detected_tokens.append(norm_text)

        if not detected_tokens:
            print("      [OCR] No valid text found after filtering.")
            return None

        candidate = "".join(detected_tokens)

        # Indian Railways 11-Digit Checksum Repair
        if len(candidate) == 11 and IndianWagonParser is not None:
            if not IndianWagonParser.validate_checksum(candidate):
                try:
                    digits = [int(d) for d in candidate]
                    s1 = sum(digits[1:10:2])
                    s2 = s1 * 3
                    s3 = sum(digits[0:10:2])
                    s4 = s2 + s3
                    expected_check = (10 - (s4 % 10)) % 10
                    repaired = candidate[:10] + str(expected_check)
                    if IndianWagonParser.validate_checksum(repaired):
                        print(f"      [OCR Repair] Check digit corrected {candidate[-1]} -> {expected_check}")
                        candidate = repaired
                except Exception:
                    pass

        print(f"      [Final Selection] {candidate}")
        return candidate