import cv2
import numpy as np
import onnxruntime as ort
from pathlib import Path
from typing import Dict, Tuple
from app.domain.enums import Emotion

# Hardcoded for now, or load from config
EMOTION_CLASSES = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

class FaceEmotionService:
    def __init__(self, model_path: str = "models/inference/emotion_classifier2.onnx"):
        self.model_path = Path(model_path)
        self.session = None
        self.input_name = None
        self.output_name = None
        self._load_model()

    def _load_model(self):
        # In a real app, ensure path is absolute relative to root CWD
        if not self.model_path.exists():
            # For demo purposes, we might not have the file at the exact new location yet
            pass 

        try:
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
            self.session = ort.InferenceSession(
                str(self.model_path),
                sess_options=sess_options,
                providers=["CPUExecutionProvider"]
            )
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
        except Exception as e:
            print(f"Failed to load ONNX model: {e}")

    def preprocess(self, face_img: np.ndarray, debug: bool = False) -> np.ndarray:
        """
        Preprocess face image for emotion model.
        - Resize to 224x224
        - Apply histogram equalization for lighting normalization
        - Convert BGR to RGB
        - ImageNet normalization
        """
        # Resize to model input size
        img = cv2.resize(face_img, (224, 224))
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # This helps with varying lighting conditions
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # CRITICAL: Convert BGR (OpenCV) to RGB (model expects)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Convert to float and normalize to [0, 1]
        img = img.astype(np.float32) / 255.0
        
        # ImageNet normalization (standard for pretrained models)
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img = (img - mean) / std
        
        # Debug: log input stats
        if debug:
            print(f"[DEBUG] Input shape: {img.shape}, min: {img.min():.3f}, max: {img.max():.3f}")
        
        # Transpose to (3, 224, 224) - CHW format
        img = img.transpose(2, 0, 1)
        
        # Add batch dimension -> (1, 3, 224, 224)
        img = np.expand_dims(img, axis=0)
        
        return img

    def predict(self, face_img: np.ndarray) -> Tuple[str, float]:
        """
        Input: crop face image (numpy array, BGR or RGB)
        Output: (emotion_label, confidence)
        """
        if self.session is None:
            # Fallback or error
            return "neutral", 0.0

        try:
            input_tensor = self.preprocess(face_img)
            outputs = self.session.run(
                [self.output_name],
                {self.input_name: input_tensor}
            )
            
            logits = outputs[0][0]
            exp_logits = np.exp(logits - np.max(logits))
            probabilities = exp_logits / np.sum(exp_logits)
            
            predicted_idx = np.argmax(probabilities)
            predicted_emotion = EMOTION_CLASSES[predicted_idx]
            confidence = float(probabilities[predicted_idx])
            
            return predicted_emotion, confidence
        except Exception as e:
            print(f"Inference error: {e}")
            return "neutral", 0.0
