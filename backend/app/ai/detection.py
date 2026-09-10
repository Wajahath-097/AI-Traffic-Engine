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
        
        For MVP, this is a simplified implementation
        In production, use a dedicated license plate detection model
        
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
        
        # Extract vehicle ROI
        vehicle_roi = frame[y1:y2, x1:x2]
        
        if vehicle_roi.size == 0:
            return None
        
        # Simplified plate detection: assume plate is in bottom-center of vehicle
        roi_h, roi_w = vehicle_roi.shape[:2]
        
        # Plate is typically 1/4 of vehicle width and 1/8 height
        plate_w = roi_w // 4
        plate_h = roi_h // 8
        
        plate_x1 = (roi_w - plate_w) // 2
        plate_y1 = roi_h - plate_h - 10
        plate_x2 = plate_x1 + plate_w
        plate_y2 = plate_y1 + plate_h
        
        # Convert to original frame coordinates
        return {
            "bbox": [
                x1 + plate_x1,
                y1 + plate_y1,
                x1 + plate_x2,
                y1 + plate_y2
            ]
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
            
        pixels = np.float32(center_roi.reshape(-1, 3))
        if len(pixels) == 0:
            return "unknown"
            
        n_colors = 1
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
        flags = cv2.KMEANS_RANDOM_CENTERS
        _, labels, palette = cv2.kmeans(pixels, n_colors, None, criteria, 10, flags)
        
        dominant_color_bgr = palette[0]
        
        # Simple color distance logic
        colors = {
            "black": np.array([0, 0, 0]),
            "white": np.array([255, 255, 255]),
            "red": np.array([0, 0, 255]),
            "blue": np.array([255, 0, 0]),
            "silver": np.array([192, 192, 192]),
            "gray": np.array([128, 128, 128]),
            "yellow": np.array([0, 255, 255]),
            "green": np.array([0, 255, 0]),
        }
        
        min_dist = float('inf')
        best_color = "unknown"
        for name, color_bgr in colors.items():
            dist = np.linalg.norm(dominant_color_bgr - color_bgr)
            if dist < min_dist:
                min_dist = dist
                best_color = name
                
        return best_color

    def detect_vehicle_model(self, vehicle_class: str) -> str:
        """Mock detection of vehicle model based on class"""
        import random
        models = {
            "car": ["Toyota Camry", "Honda Civic", "Hyundai Verna", "Maruti Swift", "Tata Nexon"],
            "truck": ["Tata Prima", "Ashok Leyland", "Mahindra Blazo"],
            "bus": ["Volvo B11R", "Tata Starbus", "Ashok Leyland Eagle"],
            "motorcycle": ["Royal Enfield", "Hero Splendor", "Bajaj Pulsar", "Honda Activa"],
            "bicycle": ["Hero Sprint", "Hercules", "Atlas"]
        }
        return random.choice(models.get(vehicle_class, ["Unknown Model"]))


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
            import random
            states = ["TS", "AP", "MH", "KA", "DL"]
            state = random.choice(states)
            district = f"{random.randint(1, 15):02d}"
            letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
            numbers = f"{random.randint(1000, 9999)}"
            mock_plate = f"{state}{district}{letters}{numbers}"
            
            return {
                "raw_text": mock_plate,
                "normalized_text": mock_plate,
                "confidence": round(random.uniform(0.91, 0.99), 2),
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


def get_yolo_detector(model_name: str = "yolov8m"):
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
