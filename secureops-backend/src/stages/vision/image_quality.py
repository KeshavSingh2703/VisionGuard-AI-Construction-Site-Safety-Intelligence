import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ImageQualityAnalyzer:
    """
    Analyzes frame quality to detect blur, low light, and washout.
    Returns a quality score (0.0 to 1.0) to weight downstream confidence.
    """
    def __init__(self, blur_threshold=100.0, low_light_threshold=30.0):
        self.blur_threshold = blur_threshold
        self.low_light_threshold = low_light_threshold
        
    def analyze(self, image: np.ndarray) -> float:
        """
        Analyze image quality.
        Returns: quality_score (0.0 = Unusable, 0.5 = Poor, 1.0 = Good)
        """
        if image is None or image.size == 0:
            return 0.0
            
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. Blur Detection (Laplacian Variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        is_blurry = blur_score < self.blur_threshold
        
        # 2. Lighting Detection (Mean Brightness)
        brightness = np.mean(gray)
        is_dark = brightness < self.low_light_threshold
        is_washed_out = brightness > 220
        
        # Scoring Logic
        # User suggested: {0, 0.5, 1.0}
        
        if is_blurry:
            # If extremely blurry, score 0.0 (Ignore)
            if blur_score < (self.blur_threshold / 2):
                return 0.0
            return 0.5
            
        if is_dark or is_washed_out:
            return 0.5
            
        return 1.0
