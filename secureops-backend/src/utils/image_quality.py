import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ImageQualityChecker:
    """
    Analyzes image quality metrics to gate low-quality frames from downstream classification.
    """
    
    def __init__(self, blur_threshold: float = 100.0, min_brightness: float = 30.0):
        """
        Args:
            blur_threshold: Laplacian variance threshold. Below this = blurry.
            min_brightness: Average pixel intensity threshold. Below this = too dark.
        """
        self.blur_threshold = blur_threshold
        self.min_brightness = min_brightness
        
    def analyze(self, image: np.ndarray):
        """
        Analyze image for blur and brightness.
        Returns:
            dict: {'is_valid': bool, 'blur_score': float, 'brightness': float, 'reason': str}
        """
        if image is None or image.size == 0:
            return {'is_valid': False, 'blur_score': 0, 'brightness': 0, 'reason': "Empty image"}
            
        # Convert to grayscale for metrics
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 1. Blur Detection (Laplacian Variance)
        # High variance = sharp edges. Low variance = blur.
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 2. Brightness Check
        brightness = np.mean(gray)
        
        is_blurry = blur_score < self.blur_threshold
        is_dark = brightness < self.min_brightness
        
        is_valid = not (is_blurry or is_dark)
        reason = ""
        if is_blurry:
            reason += f"Blurry ({blur_score:.1f} < {self.blur_threshold}); "
        if is_dark:
            reason += f"Dark ({brightness:.1f} < {self.min_brightness}); "
            
        return {
            "is_valid": is_valid,
            "blur_score": blur_score,
            "brightness": brightness,
            "reason": reason.strip()
        }
