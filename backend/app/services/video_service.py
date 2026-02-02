import cv2
import threading
import time
from app.pipelines.video_pipeline import VideoPipeline

class VideoService:
    def __init__(self):
        self.cap = None
        self.is_recording = False
        self.pipeline = VideoPipeline()
        self.capture_thread = None
        self.session_id = None

    def start_session(self, camera_id=0, session_id: str = None):
        if self.is_recording:
            return
        
        self.session_id = session_id or f"video_{int(time.time())}"
        
        try:
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                print(f"[ERROR] Failed to open camera {camera_id}")
                return
            
            # 3. Optimize Video Capture (640x480 @ 15fps)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            
            self.is_recording = True
            
            # Start pipeline worker with session_id
            self.pipeline.start(session_id=self.session_id)
            print(f"[INFO] Video pipeline started at {self.pipeline.start_time}")
            
            # Sync with SessionManager
            from app.services.session_manager import get_session_manager
            get_session_manager().update_video(
                self.session_id,
                is_recording=True,
            )
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
        except Exception as e:
            print(f"[ERROR] Failed to start video session: {e}")
            self.is_recording = False

    def stop_session(self):
        self.is_recording = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
            
        if self.cap:
            self.cap.release()
        
        # Get final stats BEFORE stopping pipeline (to avoid race condition)
        stats = self.pipeline.get_summary()
        print(f"[INFO] Video session stopped.")
        print(f"[DEBUG] Stats: total_frames={stats.get('total_frames', 0)}, counts={stats.get('counts', {})}")
        
        self.pipeline.stop()
        
        # Sync with SessionManager
        if self.session_id:
            from app.services.session_manager import get_session_manager
            get_session_manager().update_video(
                self.session_id,
                is_recording=False,
                total_frames=stats.get('total_frames', 0),
                emotion_counts=stats.get('counts', {}),
                duration=stats.get('duration_sec', 0),
            )
        
        return stats

    def _capture_loop(self):
        frame_count = 0
        print(f"[VIDEO] Capture loop started, camera open={self.cap.isOpened()}")
        
        while self.is_recording and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print(f"[VIDEO] Failed to read frame")
                break
            
            # Feed to pipeline
            self.pipeline.enqueue(frame)
            frame_count += 1
            
            if frame_count % 50 == 0:  # Log every 50 frames
                print(f"[VIDEO] Captured {frame_count} frames, pipeline.total_processed={self.pipeline.total_processed}")
            
            # Control FPS to ~15 manually to be safe
            time.sleep(1.0 / 15.0)
        
        print(f"[VIDEO] Capture loop ended, total captured: {frame_count}")

    def get_stats(self):
        # Return aggregated stats from pipeline
        return self.pipeline.get_summary()

    def get_frame(self):
        return self.pipeline.get_latest_processed_frame()
