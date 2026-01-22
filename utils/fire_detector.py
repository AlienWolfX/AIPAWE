"""
AIPAWE - Fire Detection Module
YOLOv11-based fire detection with camera input
"""

import cv2
import numpy as np
import time
from typing import List, Tuple, Optional
from dataclasses import dataclass

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


@dataclass
class FireDetection:
    """Fire detection result"""
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    center: Tuple[int, int]  # (x, y) center coordinates
    azimuth: float  # Calculated azimuth angle
    elevation: float  # Calculated elevation angle


class FireDetector:
    """YOLOv11-based fire detection system"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
        # Detection parameters
        self.model_path = config.get('detection', 'model_path')
        self.confidence_threshold = config.get('detection', 'confidence_threshold', default=0.65)
        self.min_confidence = config.get('safety', 'min_confidence', default=0.5)
        self.input_size = config.get('detection', 'input_size', default=640)
        self.device = config.get('detection', 'device', default='cpu')
        
        # Camera parameters
        self.camera_index = config.get('detection', 'camera_index', default=0)
        self.frame_width = config.get('detection', 'frame_width', default=640)
        self.frame_height = config.get('detection', 'frame_height', default=480)
        self.fps = config.get('detection', 'fps', default=15)
        
        # Camera field of view (adjust based on actual camera)
        self.horizontal_fov = 60.0  # degrees
        self.vertical_fov = 45.0    # degrees
        
        # Initialize model
        self.model = None
        if YOLO_AVAILABLE:
            try:
                self.model = YOLO(self.model_path)
                self.logger.info(f"YOLOv11 model loaded: {self.model_path}")
            except Exception as e:
                self.logger.error(f"Failed to load YOLO model: {e}")
        else:
            self.logger.warning("Ultralytics YOLO not available - detection disabled")
        
        # Initialize camera
        self.camera = None
        self._init_camera()
        
        # State
        self.last_frame = None
        self.last_detections: List[FireDetection] = []
    
    def _init_camera(self):
        """Initialize camera"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            if self.camera.isOpened():
                self.logger.info(f"Camera initialized: {self.frame_width}x{self.frame_height} @ {self.fps}fps")
            else:
                self.logger.error("Failed to open camera")
                self.camera = None
        except Exception as e:
            self.logger.error(f"Camera initialization error: {e}")
            self.camera = None
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture single frame from camera"""
        if self.camera is None or not self.camera.isOpened():
            return None
        
        ret, frame = self.camera.read()
        if ret:
            self.last_frame = frame
            return frame
        return None
    
    def _calculate_angles(self, center_x: int, center_y: int) -> Tuple[float, float]:
        """
        Calculate azimuth and elevation angles from pixel coordinates
        
        Args:
            center_x: X coordinate of detection center
            center_y: Y coordinate of detection center
            
        Returns:
            (azimuth, elevation) in degrees
        """
        # Normalize to -0.5 to 0.5 range
        norm_x = (center_x / self.frame_width) - 0.5
        norm_y = 0.5 - (center_y / self.frame_height)  # Invert Y
        
        # Calculate angles
        azimuth = norm_x * self.horizontal_fov
        elevation = norm_y * self.vertical_fov
        
        return (azimuth, elevation)
    
    def detect_fires(self, frame: np.ndarray = None) -> List[FireDetection]:
        """
        Detect fires in frame
        
        Args:
            frame: Input frame (if None, captures from camera)
            
        Returns:
            List of fire detections above confidence threshold
        """
        if frame is None:
            frame = self.capture_frame()
        
        if frame is None:
            return []
        
        if self.model is None:
            return []
        
        detections = []
        
        try:
            # Run inference
            results = self.model(frame, imgsz=self.input_size, device=self.device, verbose=False)
            
            # Process detections
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    confidence = float(box.conf[0])
                    
                    # Filter by confidence
                    if confidence < self.min_confidence:
                        continue
                    
                    # Get bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    width = x2 - x1
                    height = y2 - y1
                    
                    # Calculate center
                    center_x = x1 + width // 2
                    center_y = y1 + height // 2
                    
                    # Calculate angles
                    azimuth, elevation = self._calculate_angles(center_x, center_y)
                    
                    detection = FireDetection(
                        confidence=confidence,
                        bbox=(x1, y1, width, height),
                        center=(center_x, center_y),
                        azimuth=azimuth,
                        elevation=elevation
                    )
                    
                    detections.append(detection)
            
            # Sort by confidence (highest first)
            detections.sort(key=lambda d: d.confidence, reverse=True)
            
            # Filter by threshold
            detections = [d for d in detections if d.confidence >= self.confidence_threshold]
            
            self.last_detections = detections
            
        except Exception as e:
            self.logger.error(f"Detection error: {e}")
            return []
        
        return detections
    
    def get_highest_confidence_fire(self) -> Optional[FireDetection]:
        """Get fire detection with highest confidence"""
        if not self.last_detections:
            return None
        return self.last_detections[0]
    
    def draw_detections(self, frame: np.ndarray, detections: List[FireDetection]) -> np.ndarray:
        """Draw detection bounding boxes on frame"""
        output = frame.copy()
        
        for det in detections:
            x, y, w, h = det.bbox
            
            # Color based on confidence (green to red)
            color = (0, int(255 * (1 - det.confidence)), int(255 * det.confidence))
            
            # Draw box
            cv2.rectangle(output, (x, y), (x + w, y + h), color, 2)
            
            # Draw center
            cv2.circle(output, det.center, 5, color, -1)
            
            # Draw label
            label = f"{det.confidence:.2%} Az:{det.azimuth:.1f}° El:{det.elevation:.1f}°"
            cv2.putText(output, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return output
    
    def save_detection_frame(self, filepath: str):
        """Save last frame with detections drawn"""
        if self.last_frame is not None and self.last_detections:
            annotated = self.draw_detections(self.last_frame, self.last_detections)
            cv2.imwrite(filepath, annotated)
    
    def cleanup(self):
        """Release camera resources"""
        if self.camera is not None:
            self.camera.release()
