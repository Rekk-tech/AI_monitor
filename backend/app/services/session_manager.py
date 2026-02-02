"""
Session Manager - Single Source of Truth for Session State
Provides centralized state management for all sessions.
"""

import threading
from datetime import datetime
from typing import Dict, Optional, Any

from app.domain.session_state import SessionState, AudioState, VideoState, AgentState


class SessionManager:
    """
    Singleton session manager that maintains all active session states.
    
    Usage:
        manager = get_session_manager()
        state = manager.create("session-123")
        manager.update_audio("session-123", amplitude=0.5, is_speech=True)
        state = manager.get("session-123")
    """
    
    _instance: Optional["SessionManager"] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> "SessionManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.sessions: Dict[str, SessionState] = {}
        self._session_lock = threading.Lock()
        self._callbacks: Dict[str, list] = {}  # session_id -> list of callbacks
        print("[SessionManager] Initialized")

    # =========================
    # CRUD Operations
    # =========================
    
    def get(self, session_id: str) -> Optional[SessionState]:
        """Get session state by ID, returns None if not found"""
        with self._session_lock:
            return self.sessions.get(session_id)
    
    def create(self, session_id: str) -> SessionState:
        """Create a new session state"""
        with self._session_lock:
            if session_id in self.sessions:
                print(f"[SessionManager] Session {session_id} already exists, returning existing")
                return self.sessions[session_id]
            
            state = SessionState(
                session_id=session_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.sessions[session_id] = state
            print(f"[SessionManager] Created session: {session_id}")
            return state
    
    def delete(self, session_id: str) -> bool:
        """Delete a session state"""
        with self._session_lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                if session_id in self._callbacks:
                    del self._callbacks[session_id]
                print(f"[SessionManager] Deleted session: {session_id}")
                return True
            return False
    
    def get_or_create(self, session_id: str) -> SessionState:
        """Get existing session or create new one"""
        state = self.get(session_id)
        if state is None:
            state = self.create(session_id)
        return state

    # =========================
    # Audio State Updates
    # =========================
    
    def update_audio(
        self,
        session_id: str,
        is_recording: Optional[bool] = None,
        amplitude: Optional[float] = None,
        is_speech: Optional[bool] = None,
        status: Optional[str] = None,
        total_frames: Optional[int] = None,
        speech_frames: Optional[int] = None,
        duration: Optional[float] = None,
        file_path: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[SessionState]:
        """Update audio state for a session"""
        state = self.get_or_create(session_id)
        
        with self._session_lock:
            audio = state.audio
            
            if is_recording is not None:
                audio.is_recording = is_recording
            if amplitude is not None:
                audio.amplitude = amplitude
            if is_speech is not None:
                audio.is_speech = is_speech
            if status is not None:
                audio.status = status
            if total_frames is not None:
                audio.total_frames = total_frames
            if speech_frames is not None:
                audio.speech_frames = speech_frames
            if duration is not None:
                audio.duration = duration
            if file_path is not None:
                audio.file_path = file_path
            if result is not None:
                audio.result = result
            if error is not None:
                audio.error = error
            
            state.updated_at = datetime.now()
        
        self._notify_update(session_id, "audio")
        return state

    # =========================
    # Video State Updates
    # =========================
    
    def update_video(
        self,
        session_id: str,
        is_recording: Optional[bool] = None,
        fps: Optional[float] = None,
        total_frames: Optional[int] = None,
        face_count: Optional[int] = None,
        emotion_counts: Optional[Dict[str, int]] = None,
        dominant_emotion: Optional[str] = None,
        confidence: Optional[float] = None,
        last_emotions: Optional[list] = None,
        boxes: Optional[list] = None,
        duration: Optional[float] = None,
    ) -> Optional[SessionState]:
        """Update video state for a session"""
        state = self.get_or_create(session_id)
        
        with self._session_lock:
            video = state.video
            
            if is_recording is not None:
                video.is_recording = is_recording
            if fps is not None:
                video.fps = fps
            if total_frames is not None:
                video.total_frames = total_frames
            if face_count is not None:
                video.face_count = face_count
            if emotion_counts is not None:
                video.emotion_counts = emotion_counts
            if dominant_emotion is not None:
                video.dominant_emotion = dominant_emotion
            if confidence is not None:
                video.confidence = confidence
            if last_emotions is not None:
                video.last_emotions = last_emotions
            if boxes is not None:
                video.boxes = boxes
            if duration is not None:
                video.duration = duration
            
            state.updated_at = datetime.now()
        
        self._notify_update(session_id, "video")
        return state

    # =========================
    # Agent State Updates
    # =========================
    
    def update_agent(
        self,
        session_id: str,
        final_state: Optional[str] = None,
        confidence: Optional[Dict[str, float]] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> Optional[SessionState]:
        """Update agent state for a session"""
        state = self.get_or_create(session_id)
        
        with self._session_lock:
            agent = state.agent
            
            if final_state is not None:
                agent.final_state = final_state
            if confidence is not None:
                agent.confidence = confidence
            if result is not None:
                agent.result = result
            
            state.updated_at = datetime.now()
        
        self._notify_update(session_id, "agent")
        return state

    # =========================
    # Convenience Methods
    # =========================
    
    def get_audio_state(self, session_id: str) -> Optional[AudioState]:
        """Get just the audio state for a session"""
        state = self.get(session_id)
        return state.audio if state else None
    
    def get_video_state(self, session_id: str) -> Optional[VideoState]:
        """Get just the video state for a session"""
        state = self.get(session_id)
        return state.video if state else None
    
    def get_agent_state(self, session_id: str) -> Optional[AgentState]:
        """Get just the agent state for a session"""
        state = self.get(session_id)
        return state.agent if state else None
    
    def list_sessions(self) -> list:
        """List all active session IDs"""
        with self._session_lock:
            return list(self.sessions.keys())

    # =========================
    # Callback System (for WS)
    # =========================
    
    def register_callback(self, session_id: str, callback: callable):
        """Register a callback for state updates"""
        if session_id not in self._callbacks:
            self._callbacks[session_id] = []
        self._callbacks[session_id].append(callback)
    
    def unregister_callback(self, session_id: str, callback: callable):
        """Unregister a callback"""
        if session_id in self._callbacks:
            try:
                self._callbacks[session_id].remove(callback)
            except ValueError:
                pass
    
    def _notify_update(self, session_id: str, update_type: str):
        """Notify callbacks of state update"""
        if session_id in self._callbacks:
            state = self.get(session_id)
            for callback in self._callbacks[session_id]:
                try:
                    callback(session_id, update_type, state)
                except Exception as e:
                    print(f"[SessionManager] Callback error: {e}")


# =========================
# Singleton Accessor
# =========================

_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the singleton SessionManager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
