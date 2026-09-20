"""
AI and ML services for vehicle detection and OCR
"""

from typing import Optional, Tuple, List
import logging
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class YOLODetector:
    """Vehicle detection using YOLOv8"""
    
    def __init__(self, model_name: str = "yolov8m"):
        """Initialize YOLOv8 detector"""
        try:
            import torch
            
            # Monkeypatch torch.load for PyTorch 2.6+ to fix ultralytics loading error
            original_load = torch.load
            def safe_load(*args, **kwargs):
                kwargs['weights_only'] = False
                return original_load(*args, **kwargs)
            torch.load = safe_load
            
            from ultralytics import YOLO
            
            self.model = YOLO(f"{model_name}.pt")
            logger.info(f"YOLOv8 model {model_name} loaded successfully")
        except ImportError:
            logger.warning("YOLOv8 not installed, running in mock mode")
            self.model = None
    
    def detect_vehicles(
        self,
        frame: np.ndarray,
        confidence_threshold: float = 0.5
    ) -> List[dict]:
        """
        Detect vehicles in a frame
        
        Args:
            frame: Input frame as numpy array
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            List of detections with class, confidence, and bounding box
        """
        if self.model is None:
            return []
        
        try:
            results = self.model(frame, conf=confidence_threshold, verbose=False)
            
            detections = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Get class names
                    class_name = r.names.get(cls_id, "unknown")
                    
                    # Filter for vehicles
                    if class_name in ["car", "truck", "bus", "motorcycle", "bicycle"]:
                        coords = box.xyxy[0].tolist()
                        x1, y1, x2, y2 = coords
                        
                        # Heuristic for "autorickshaw": 
                        # In India, auto-rickshaws are often misclassified by COCO models as trucks, cars, or motorcycles.
                        # They typically have a squarish aspect ratio (close to 1:1) from the front/back
                        width = x2 - x1
                        height = y2 - y1
                        if width > 0 and height > 0:
                            aspect_ratio = width / height
                            # If it's classified as a truck/car, but is relatively small and boxy, it might be an auto
                            if class_name in ["truck", "car"] and 0.8 < aspect_ratio < 1.25 and height < frame.shape[0] * 0.4:
                                class_name = "autorickshaw"
                        
                        detections.append({
                            "class": class_name,
                            "confidence": conf,
                            "bbox": coords,  # [x1, y1, x2, y2]
                            "class_id": cls_id
                        })
            
            return detections
            
        except Exception as e:
            logger.error(f"Error in vehicle detection: {e}")
            return []
    
    def detect_plates(
        self,
        frame: np.ndarray,
        vehicle_bbox: Tuple[float, float, float, float]
    ) -> Optional[dict]:
        """
        Detect license plate region in vehicle area
        
        Uses heuristics (bottom half, center) to improve OCR accuracy.
        
        Args:
            frame: Input frame
            vehicle_bbox: Vehicle bounding box [x1, y1, x2, y2]
            
        Returns:
            Plate region with coordinates
        """
        x1, y1, x2, y2 = vehicle_bbox
        h, w = frame.shape[:2]
        
        # Clamp coordinates
        x1, y1 = max(0, int(x1)), max(0, int(y1))
        x2, y2 = min(w, int(x2)), min(h, int(y2))
        
        # Heuristic: plates are usually in the lower 50% and horizontally centered
        v_h = y2 - y1
        v_w = x2 - x1
        
        # Avoid zero size
        if v_h < 10 or v_w < 10:
            return None
            
        px1 = int(x1 + v_w * 0.1)
        py1 = int(y1 + v_h * 0.5)
        px2 = int(x2 - v_w * 0.1)
        py2 = y2
        
        plate_roi = frame[py1:py2, px1:px2]
        
        if plate_roi.size == 0:
            return None
        
        return {
            "bbox": [px1, py1, px2, py2]
        }

    def detect_color(self, frame: np.ndarray, vehicle_bbox: Tuple[float, float, float, float]) -> str:
        """Detect dominant color of vehicle"""
        import cv2
        x1, y1, x2, y2 = vehicle_bbox
        h, w = frame.shape[:2]
        x1, y1 = max(0, int(x1)), max(0, int(y1))
        x2, y2 = min(w, int(x2)), min(h, int(y2))
        
        vehicle_roi = frame[y1:y2, x1:x2]
        if vehicle_roi.size == 0:
            return "unknown"
            
        # Crop the center 50% to avoid background
        roi_h, roi_w = vehicle_roi.shape[:2]
        cx1, cy1 = roi_w // 4, roi_h // 4
        cx2, cy2 = roi_w * 3 // 4, roi_h * 3 // 4
        center_roi = vehicle_roi[cy1:cy2, cx1:cx2]
        
        if center_roi.size == 0:
            center_roi = vehicle_roi
            
        # Convert to HSV for better color detection
        hsv_roi = cv2.cvtColor(center_roi, cv2.COLOR_BGR2HSV)
        
        # Define color ranges in HSV
        color_ranges = {
            "red": [
                (np.array([0, 100, 100]), np.array([10, 255, 255])),
                (np.array([160, 100, 100]), np.array([180, 255, 255]))
            ],
            "blue": [(np.array([100, 100, 50]), np.array([130, 255, 255]))],
            "green": [(np.array([35, 50, 50]), np.array([85, 255, 255]))],
            "yellow": [(np.array([20, 100, 100]), np.array([35, 255, 255]))],
            "white": [(np.array([0, 0, 200]), np.array([180, 30, 255]))],
            "black": [(np.array([0, 0, 0]), np.array([180, 255, 40]))],
            "silver": [(np.array([0, 0, 150]), np.array([180, 20, 200]))],
            "gray": [(np.array([0, 0, 40]), np.array([180, 40, 150]))]
        }
        
        max_count = 0
        best_color = "unknown"
        
        for color_name, ranges in color_ranges.items():
            mask = np.zeros(hsv_roi.shape[:2], dtype=np.uint8)
            for lower, upper in ranges:
                mask |= cv2.inRange(hsv_roi, lower, upper)
            
            count = cv2.countNonZero(mask)
            if count > max_count:
                max_count = count
                best_color = color_name
                
        # Only return color if it makes up a significant portion of the ROI
        total_pixels = hsv_roi.shape[0] * hsv_roi.shape[1]
        if max_count > total_pixels * 0.1:
            return best_color
            
        return "unknown"



class OCREngine:
    """License plate OCR using PaddleOCR"""
    
    def __init__(self, language: str = "en"):
        """Initialize OCR engine"""
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(use_angle_cls=True, lang=language)
            self.language = language
            logger.info(f"PaddleOCR initialized for language: {language}")
        except Exception as e:
            logger.warning(f"PaddleOCR not fully installed or failed to init ({e}), running in mock mode")
            self.ocr = None
            self.language = language
    
    def recognize_plate(
        self,
        frame: np.ndarray,
        plate_bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> dict:
        """
        Recognize license plate text
        
        Args:
            frame: Input frame
            plate_bbox: Optional plate region [x1, y1, x2, y2]
            
        Returns:
            OCR result with text and confidence
        """
        if self.ocr is None:
            return {
                "raw_text": "",
                "normalized_text": "",
                "confidence": 0.0,
                "engine": "paddleocr"
            }
        
        try:
            # Extract plate ROI if provided
            if plate_bbox:
                x1, y1, x2, y2 = plate_bbox
                h, w = frame.shape[:2]
                x1, y1 = max(0, int(x1)), max(0, int(y1))
                x2, y2 = min(w, int(x2)), min(h, int(y2))
                plate_img = frame[y1:y2, x1:x2]
            else:
                plate_img = frame
            
            if plate_img.size == 0:
                return {
                    "raw_text": "",
                    "normalized_text": "",
                    "confidence": 0.0,
                    "engine": "paddleocr"
                }
            
            # Run OCR
            results = self.ocr.ocr(plate_img, cls=True)
            
            if not results or not results[0]:
                return {
                    "raw_text": "",
                    "normalized_text": "",
                    "confidence": 0.0,
                    "engine": "paddleocr"
                }
            
            # Extract text and confidence
            texts = []
            confidences = []
            
            for line in results:
                for word_info in line:
                    text, conf = word_info[1], word_info[2]
                    texts.append(text)
                    confidences.append(conf)
            
            raw_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Normalize plate (remove spaces and convert to uppercase)
            normalized = raw_text.upper().replace(" ", "").replace("-", "")
            
            return {
                "raw_text": raw_text,
                "normalized_text": normalized,
                "confidence": avg_confidence,
                "engine": "paddleocr",
                "language": self.language
            }
            
        except Exception as e:
            logger.error(f"Error in OCR: {e}")
            return {
                "raw_text": "",
                "normalized_text": "",
                "confidence": 0.0,
                "engine": "paddleocr"
            }
    
    def recheck_ocr(
        self,
        frame: np.ndarray,
        plate_bbox: Tuple[float, float, float, float]
    ) -> dict:
        """
        Re-check OCR with preprocessing (for low confidence results)
        
        Args:
            frame: Input frame
            plate_bbox: Plate region coordinates
            
        Returns:
            OCR result after preprocessing
        """
        try:
            # Extract plate
            x1, y1, x2, y2 = plate_bbox
            h, w = frame.shape[:2]
            x1, y1 = max(0, int(x1)), max(0, int(y1))
            x2, y2 = min(w, int(x2)), min(h, int(y2))
            plate_img = frame[y1:y2, x1:x2]
            
            # Apply preprocessing: contrast enhancement
            import cv2
            # Convert to grayscale
            if len(plate_img.shape) == 3:
                gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = plate_img
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Run OCR on enhanced image
            results = self.ocr.ocr(enhanced, cls=True)
            
            if not results or not results[0]:
                return {
                    "raw_text": "",
                    "normalized_text": "",
                    "confidence": 0.0,
                    "engine": "paddleocr",
                    "preprocessed": True
                }
            
            # Extract results
            texts = []
            confidences = []
            
            for line in results:
                for word_info in line:
                    text, conf = word_info[1], word_info[2]
                    texts.append(text)
                    confidences.append(conf)
            
            raw_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            normalized = raw_text.upper().replace(" ", "").replace("-", "")
            
            return {
                "raw_text": raw_text,
                "normalized_text": normalized,
                "confidence": avg_confidence,
                "engine": "paddleocr",
                "language": self.language,
                "preprocessed": True
            }
            
        except Exception as e:
            logger.error(f"Error in OCR recheck: {e}")
            return {
                "raw_text": "",
                "normalized_text": "",
                "confidence": 0.0,
                "engine": "paddleocr",
                "preprocessed": True
            }


# Singleton instances
_yolo_detector = None
_ocr_engine = None


def get_yolo_detector(model_name: str = "yolov8n"):
    """Get or create YOLO detector instance"""
    global _yolo_detector
    if _yolo_detector is None:
        _yolo_detector = YOLODetector(model_name)
    return _yolo_detector


def get_ocr_engine(language: str = "en"):
    """Get or create OCR engine instance"""
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = OCREngine(language)
    return _ocr_engine
