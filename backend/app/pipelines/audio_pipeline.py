import librosa
from typing import Dict
from app.services.speech_emotion_service import SpeechEmotionService

class AudioPipeline:
    def __init__(self, speech_service):
        self.speech_service = speech_service
        self.chunk_duration = 3.0
        self.sr = 16000

    def run(self, audio_path: str) -> Dict[str, float]:
        """
        Session-level inference
        """
        # Load full audio
        audio, sr = librosa.load(audio_path, sr=self.sr)

        if len(audio) < self.sr * 2:
            # < 2s audio → unreliable
            return {
                "satisfied": 0.5,
                "dissatisfied": 0.5,
                "confidence": 0.0,
                "note": "audio too short"
            }

        # One-shot inference
        result = self.speech_service.predict(audio)

        satisfied = result.get("satisfied", 0.0)
        dissatisfied = result.get("dissatisfied", 0.0)

        return {
            "satisfied": round(satisfied, 3),
            "dissatisfied": round(dissatisfied, 3),
            "confidence": round(result["confidence"], 3)
        }
