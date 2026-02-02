import torch
import numpy as np
import librosa
import json
from pathlib import Path
from transformers import (
    AutoConfig,
    AutoModelForAudioClassification,
    AutoFeatureExtractor,
)

class SpeechEmotionService:
    def __init__(self, model_dir: str = "models/inference"):
        self.model_dir = Path(model_dir)
        self.device = torch.device("cpu")

        self.sampling_rate = 16000
        self.model = None
        self.feature_extractor = None
        self.id2label = {}

        self._load_model()

    def _load_model(self):
        # Load config
        config = AutoConfig.from_pretrained(self.model_dir)
        self.id2label = {int(k): v for k, v in config.id2label.items()}

        # Load feature extractor
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(
            self.model_dir,
            local_files_only=True
        )

        # Load model (uses model.safetensors automatically)
        self.model = AutoModelForAudioClassification.from_pretrained(
            self.model_dir,
            config=config,
            local_files_only=True
        )

        self.model.to(self.device)
        self.model.eval()

        print("✅ Speech Emotion model loaded (session-level)")

    @torch.no_grad()
    def predict(self, audio: np.ndarray) -> dict:
        """
        audio: numpy array (full session audio, 16kHz)
        """
        inputs = self.feature_extractor(
            audio,
            sampling_rate=self.sampling_rate,
            return_tensors="pt",
            padding=True
        )

        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        logits = self.model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()

        result = {
            self.id2label[i]: float(probs[i])
            for i in range(len(probs))
        }

        # Confidence = max probability
        result["confidence"] = float(np.max(probs))

        return result
