import cv2
import numpy as np
from PIL import Image
import os
from typing import List, Tuple
import torch

class FaceDetectionService:
    def __init__(self, model_path: str = "models/inference/model.pt"):
        """
        Initialize YOLO Face Detection Model
        """
        self.model_path = model_path
        self.device = 'cpu'  # Force CPU for i7-1260P optimization
        
        # Load YOLO model (YOLOv5/v8/v11 format)
        try:
            # Try loading with ultralytics if available
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            self.model.to(self.device)
            print(f"✅ YOLO Face Detection loaded from {model_path}")
        except ImportError:
            # Fallback: Load with torch.hub (YOLOv5)
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=False)
            self.model.to(self.device)
            print(f"✅ YOLOv5 Face Detection loaded from {model_path}")
        
        # Optimization for CPU inference
        self.model.conf = 0.7  # Confidence threshold
        self.model.iou = 0.45  # NMS IOU threshold
    
    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in frame using YOLO.
        Returns list of (x, y, w, h)
        """
        if frame is None:
            return []
        
        # YOLO inference
        results = self.model(frame, verbose=False)
        
        # Extract bounding boxes
        faces = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get coordinates (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # Convert to (x, y, w, h) format
                x = int(x1)
                y = int(y1)
                w = int(x2 - x1)
                h = int(y2 - y1)
                
                faces.append((x, y, w, h))
        
        return faces
    
    def crop_face(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Crop face with padding for better emotion recognition.
        Uses square crop for consistent aspect ratio.
        """
        x, y, w, h = bbox
        img_h, img_w = frame.shape[:2]
        
        # Use larger square crop centered on face for better context
        # This matches typical training data augmentation
        face_size = max(w, h)
        
        # 30% padding gives forehead, chin context
        padding = 0.3
        padded_size = int(face_size * (1 + 2 * padding))
        
        # Center of face
        cx = x + w // 2
        cy = y + h // 2
        
        # Calculate crop boundaries
        x1 = max(0, cx - padded_size // 2)
        y1 = max(0, cy - padded_size // 2)
        x2 = min(img_w, x1 + padded_size)
        y2 = min(img_h, y1 + padded_size)
        
        # Adjust if hitting boundaries
        if x2 - x1 < padded_size:
            x1 = max(0, x2 - padded_size)
        if y2 - y1 < padded_size:
            y1 = max(0, y2 - padded_size)
        
        crop = frame[y1:y2, x1:x2]
        
        # Ensure non-empty crop
        if crop.size == 0:
            return frame[y:y+h, x:x+w]
        
        return crop
