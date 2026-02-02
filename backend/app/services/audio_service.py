from email.mime import audio
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import threading
import time
import os
import json
from datetime import datetime
from typing import Optional, List


class AudioService:
    """
    Audio recording service with proper attribute initialization.
    State is synchronized with SessionManager for real-time updates.
    """
    
    def __init__(self, root_data_path: str = "data"):
        # Paths
        self.root_data_path: str = root_data_path
        self.audio_path: str = os.path.join(root_data_path, "audio")
        self.logs_path: str = os.path.join(root_data_path, "logs")

        os.makedirs(self.audio_path, exist_ok=True)
        os.makedirs(self.logs_path, exist_ok=True)

        # Audio configuration
        self.sample_rate: int = 16000
        self.channels: int = 1

        # Runtime state - local copy for performance, synced to SessionManager
        self.is_recording: bool = False
        self.frames: List[np.ndarray] = []  # Keep locally for WAV generation
        self.thread: Optional[threading.Thread] = None
        self.start_time: Optional[float] = None
        self.session_id: Optional[str] = None

        # Real-time metrics (also synced to SessionManager)
        self.current_amplitude: float = 0.0
        self.total_frames: int = 0
        self.speech_frames: int = 0

        # Thread safety
        self.lock: threading.Lock = threading.Lock()
        
        # Adaptive VAD (Voice Activity Detection)
        self._noise_samples: List[float] = []
        self._noise_floor: float = 0.015  # Initial conservative threshold
        self._noise_calibrated: bool = False

    
    # =========================
    # PUBLIC API
    # =========================
    def start_recording(self, session_id: str = None):
        if self.is_recording:
            return

        self.is_recording = True
        self.frames = []
        self.start_time = time.time()
        self.session_id = session_id or f"sess_{int(time.time())}"

        self.current_amplitude = 0.0
        self.total_frames = 0
        self.speech_frames = 0
        
        # Reset noise calibration for new session
        self._noise_samples = []
        self._noise_floor = 0.015
        self._noise_calibrated = False

        # Sync with SessionManager
        from app.services.session_manager import get_session_manager
        get_session_manager().update_audio(
            self.session_id,
            is_recording=True,
            status="recording",
            amplitude=0.0,
            total_frames=0,
            speech_frames=0,
        )

        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()

        print(f"[{datetime.now()}] Audio recording started: {self.session_id}")

    def stop_recording(self) -> str:
        self.is_recording = False
        if self.thread:
            self.thread.join(timeout=2.0)

        duration = time.time() - self.start_time if self.start_time else 0.0
        if not self.frames:
            raise RuntimeError("No audio recorded")
        audio = np.concatenate(self.frames, axis=0)

        # Convert float32 → int16 WAV
        audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)

        filename = f"call_{self.session_id}.wav"
        filepath = os.path.join(self.audio_path, filename)
        wav.write(filepath, self.sample_rate, audio_int16)

        # Validation metrics
        speech_ratio = (
            self.speech_frames / self.total_frames
            if self.total_frames > 0 else 0.0
        )

        valid = duration >= 10.0 and speech_ratio >= 0.2

        metadata = {
            "session_id": self.session_id,
            "duration": round(duration, 2),
            "speech_ratio": round(speech_ratio, 3),
            "sample_rate": self.sample_rate,
            "timestamp": datetime.now().isoformat(),
            "file_path": filepath,
            "valid": valid
        }

        meta_path = os.path.join(self.logs_path, f"call_{self.session_id}.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"[{datetime.now()}] Audio saved: {filepath}")

        # Sync with SessionManager
        from app.services.session_manager import get_session_manager
        get_session_manager().update_audio(
            self.session_id,
            is_recording=False,
            status="processing",
            duration=round(duration, 2),
            file_path=filepath,
            total_frames=self.total_frames,
            speech_frames=self.speech_frames,
        )

        return filepath


    # =========================
    # INTERNAL
    # =========================
    def _record_loop(self):
        # Import here to avoid circular imports
        from app.services.session_manager import get_session_manager
        from app.services.event_broadcaster import schedule_broadcast_audio_metrics
        session_manager = get_session_manager()
        sync_counter = 0  # Sync every N frames to reduce overhead
        
        def callback(indata, frames, time_info, status):
            nonlocal sync_counter
            if not self.is_recording:
                return

            rms = np.sqrt(np.mean(indata ** 2))
            amp = min(float(rms * 5.0), 1.0)
            
            # Adaptive VAD: calibrate noise floor from first ~20 frames (~2 seconds)
            with self.lock:
                if not self._noise_calibrated:
                    self._noise_samples.append(amp)
                    if len(self._noise_samples) >= 20:
                        # Set noise floor as average of calibration samples
                        self._noise_floor = sum(self._noise_samples) / len(self._noise_samples)
                        self._noise_calibrated = True
                        print(f"[AUDIO] Noise floor calibrated: {self._noise_floor:.3f}")
                
                # Use adaptive threshold: must be above noise floor * 2, minimum 0.015
                threshold = max(0.015, self._noise_floor * 2.0)
                is_speech = amp > threshold
                
                self.frames.append(indata.astype(np.float32))
                self.current_amplitude = amp
                self.total_frames += 1
                if is_speech:
                    self.speech_frames += 1
                
                # Sync to SessionManager every 10 frames (~1 second at 10fps)
                sync_counter += 1
                if sync_counter >= 10:
                    sync_counter = 0
                    duration = time.time() - self.start_time if self.start_time else 0
                    
                    session_manager.update_audio(
                        self.session_id,
                        amplitude=amp,
                        is_speech=is_speech,
                        total_frames=self.total_frames,
                        speech_frames=self.speech_frames,
                    )
                    
                    # Broadcast via WebSocket (throttled at 100ms)
                    schedule_broadcast_audio_metrics(
                        self.session_id,
                        amplitude=amp,
                        is_speech=is_speech,
                        duration=duration,
                        total_frames=self.total_frames,
                        speech_frames=self.speech_frames,
                    )

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=callback
            ):
                while self.is_recording:
                    sd.sleep(100)
        except Exception as e:
            print(f"[AudioService] Stream error: {e}")
            self.is_recording = False
            # Update error state in SessionManager
            session_manager.update_audio(
                self.session_id,
                status="error",
                error=str(e),
            )

