import queue
import threading
import time
import cv2
import numpy as np
from typing import Dict, List, Optional
from app.services.face_emotion_service import FaceEmotionService
from app.services.face_detection_service import FaceDetectionService
from app.utils.face_preprocess import align_face, normalize_face


class VideoPipeline:
    def __init__(self):
        # 6. Queue & Memory Limit (maxsize=2)
        self.frame_queue = queue.Queue(maxsize=2)
        self.result_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        
        # Session tracking
        self.session_id: Optional[str] = None
        
        # Thread safety & Data
        self.processed_lock = threading.Lock()
        self.latest_frame = None
        self.latest_processed_frame = None
        self.emotion_window = [] # For smoothing
        
        # Services
        self.detection_service = FaceDetectionService()
        self.emotion_service = FaceEmotionService()
        
        # Aggregation state
        self.emotion_counts = {
            "angry": 0, "disgust": 0, "fear": 0, "happy": 0, 
            "sad": 0, "surprise": 0, "neutral": 0
        }
        self.total_processed = 0

        # Optimization State
        self.last_inference_time = 0
        self.inference_interval = 1.0 / 5.0 # Target 5 FPS for inference
        self.last_faces = []
        self.last_emotions = []
        self.last_confs = []
        
        # Confidence smoothing (EMA) - lower alpha = smoother
        self._confidence_ema = 0.0
        self._confidence_alpha = 0.2  # Smoothed for stability
        
        # Emotion stability - require consistent detection
        self._emotion_history = []
        self._emotion_history_size = 5  # Average over 5 frames

    def start(self, session_id: str = None):
        self.session_id = session_id
        
        # Reset stats on start
        self.emotion_counts = {
            "angry": 0, "disgust": 0, "fear": 0, "happy": 0, 
            "sad": 0, "surprise": 0, "neutral": 0
        }
        self.total_processed = 0
        self.timeline = [] # List of {"timestamp": float, "emotion": str, "confidence": float}
        self.start_time = time.time()
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.worker_thread.start()


    def get_summary(self) -> Dict:
        duration_sec = int(time.time() - self.start_time) if hasattr(self, 'start_time') else 0
        
        if self.total_processed == 0:
            return {
                "counts": {},
                "timeline": [],
                "duration_sec": duration_sec,
                "total_frames": 0
            }
        
        # Return percentages
        counts = {k: round((v / self.total_processed) * 100, 1) for k, v in self.emotion_counts.items()}
        return {
            "counts": counts,
            "timeline": self.timeline,
            "duration_sec": duration_sec,
            "total_frames": self.total_processed
        }

    def stop(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()

    def enqueue(self, frame: np.ndarray):
        if not self.running:
            return
        
        with self.processed_lock:
            self.latest_frame = frame
            
        try:
            # removing old frames if full to maintain realtime
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            self.frame_queue.put(frame, timeout=0.01)
        except queue.Full:
            pass

    def get_latest_processed_frame(self):
        with self.processed_lock:
            if self.latest_processed_frame is not None:
                return self.latest_processed_frame.copy()
            return None

    def _render_overlay(self, frame, faces, emotions, confidences):
        """Draw bounding boxes and UI overlays"""
        canvas = frame.copy()
        h, w = canvas.shape[:2]
        
        # 1. Draw Faces
        for i, (x, y, fw, fh) in enumerate(faces):
            label = emotions[i].upper()
            color = (0, 255, 0) if label == "HAPPY" else (0, 0, 255) if label in ["ANGRY", "SAD"] else (255, 255, 0)
            
            # Box
            cv2.rectangle(canvas, (x, y), (x+fw, y+fh), color, 2)
            
            # Label background
            text = f"Emotion: {label}"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(canvas, (x, y - 25), (x + tw + 10, y), color, -1)
            cv2.putText(canvas, text, (x + 5, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 1)

        # 2. Draw Dashboard Overlay (Top Left)
        # Background for stats
        cv2.rectangle(canvas, (10, 10), (250, 100), (0, 0, 0), -1)
        cv2.rectangle(canvas, (10, 10), (250, 100), (255, 255, 255), 1)
        
        # Calculate Dominant Emotion (Last N frames)
        if self.emotion_window:
            from collections import Counter
            counts = Counter(self.emotion_window)
            dominant = counts.most_common(1)[0][0].upper()
        else:
            dominant = "WAITING..."
            
        cv2.putText(canvas, "LIVE MONITORING", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(canvas, f"Dominant (10s): {dominant}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Trend (Naive implementation)
        trend = "Stable"
        cv2.putText(canvas, f"Trend: {trend}", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        return canvas

    def _process_loop(self):
        # Import here to avoid circular imports
        from app.services.session_manager import get_session_manager
        from app.services.event_broadcaster import schedule_broadcast_video_stats
        session_manager = get_session_manager()
        
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            
            # 3. Optimize Realtime Video
            # Only run inference if interval passed
            now = time.time()
            if now - self.last_inference_time > self.inference_interval:
                # Detect
                faces = self.detection_service.detect(frame)
                
                current_emotions = []
                current_confs = []
                
                for bbox in faces:
                    face_img = self.detection_service.crop_face(frame, bbox)

                    # ===== PREPROCESS (OPTIMIZED) =====
                    # CLAHE normalization is fast (~2ms) and improves accuracy
                    # Face alignment with MediaPipe is slow (~50ms), skip for FPS
                    try:
                        # normalize_face is fast and helps with lighting variations
                        face_img = normalize_face(face_img)
                        # align_face is slow - skip for real-time performance
                        # face_img = align_face(face_img)
                    except Exception:
                        pass  # Continue with original crop if preprocessing fails

                    emotion, conf = self.emotion_service.predict(face_img)

                    current_emotions.append(emotion)
                    current_confs.append(conf)
                    
                    # Update aggregation - lowered threshold for better detection rate
                    if conf > 0.3:  # Lower threshold = more detections counted
                        self.emotion_counts[emotion] = self.emotion_counts.get(emotion, 0) + 1
                        self.total_processed += 1
                        # Add to timeline
                        self.timeline.append({
                            "timestamp": time.time() - self.start_time,
                            "emotion": emotion,
                            "confidence": conf
                        })
                        
                        # Update smoothing window (limit size)
                        self.emotion_window.append(emotion)
                        if len(self.emotion_window) > 100: # Keep last ~100 detections
                            self.emotion_window.pop(0)

                # Update cache
                self.last_inference_time = now
                self.last_faces = faces
                self.last_emotions = current_emotions
                self.last_confs = current_confs
                
                # Sync to SessionManager and broadcast for real-time updates
                if self.session_id:
                    # Dominant emotion: use argmax of cumulative counts for consistency with distribution
                    if self.total_processed > 0 and self.emotion_counts:
                        dominant = max(self.emotion_counts, key=self.emotion_counts.get)
                    else:
                        dominant = current_emotions[0] if current_emotions else "neutral"
                    
                    # Confidence smoothing (EMA) + cap at 95%
                    raw_conf = current_confs[0] if current_confs else 0.0
                    self._confidence_ema = (
                        self._confidence_alpha * raw_conf + 
                        (1 - self._confidence_alpha) * self._confidence_ema
                    )
                    confidence = min(self._confidence_ema, 0.95)  # Cap at 95%
                    
                    duration = time.time() - self.start_time if hasattr(self, 'start_time') else 0
                    
                    # Debug: Log detection
                    print(f"[PIPELINE] Detected {len(faces)} faces, emotion={dominant}, conf={confidence:.2f} (raw={raw_conf:.2f})")
                    
                    session_manager.update_video(
                        self.session_id,
                        face_count=len(faces),
                        dominant_emotion=dominant,
                        confidence=confidence,
                        total_frames=self.total_processed,
                        emotion_counts=self.emotion_counts.copy(),
                        boxes=[(b[0], b[1], b[2], b[3]) for b in faces],
                    )
                    
                    # Broadcast via WebSocket (throttled at 200ms)
                    schedule_broadcast_video_stats(
                        self.session_id,
                        face_count=len(faces),
                        dominant_emotion=dominant,
                        confidence=confidence,
                        total_frames=self.total_processed,
                        emotion_counts=self.emotion_counts.copy(),
                        duration=duration,
                    )
            
            # Render using (fresh frame + cached detections)
            annotated_frame = self._render_overlay(
                frame, 
                self.last_faces, 
                self.last_emotions, 
                self.last_confs
            )
            
            with self.processed_lock:
                self.latest_processed_frame = annotated_frame

    def get_summary(self) -> Dict[str, float]:
        if self.total_processed == 0:
            return {}
        
        # Return percentages
        return {k: (v / self.total_processed) * 100 for k, v in self.emotion_counts.items()}
