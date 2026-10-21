import cv2
import numpy as np

def calculate_blur_score(image: np.ndarray) -> float:
    """
    Calculates the blur score of an image using the Variance of Laplacian method.
    
    Args:
        image: Input image (numpy array).
        
    Returns:
        float: The variance of the Laplacian. Higher values indicate sharper images.
               Lower values indicate blurrier images.
    """
    # Convert to grayscale if the image is color
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Compute the Laplacian of the image and then return the variance
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def is_frame_sharp(score: float, threshold: float = 100.0) -> bool:
    """
    Determines if a frame is sharp enough based on the score and threshold.
    
    Args:
        score: The calculated blur score.
        threshold: The threshold value. Defaults to 100.0 (can be tuned).
        
    Returns:
        bool: True if score >= threshold, False otherwise.
    """
    return score >= threshold
