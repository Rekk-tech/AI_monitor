"""
Session State Data Models
Defines the data structures for centralized session state management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


@dataclass
class AudioState:
    """
    Audio recording and processing state.
    Updated by AudioService, read by WebSocket broadcaster.
    """
    is_recording: bool = False
    amplitude: float = 0.0
    is_speech: bool = False
    status: str = "idle"  # idle | recording | processing | done | error
    total_frames: int = 0
    speech_frames: int = 0
    duration: float = 0.0
    file_path: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_recording": self.is_recording,
            "amplitude": self.amplitude,
            "is_speech": self.is_speech,
            "status": self.status,
            "total_frames": self.total_frames,
            "speech_frames": self.speech_frames,
            "duration": self.duration,
            "file_path": self.file_path,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class VideoState:
    """
    Video processing state.
    Updated by VideoPipeline, read by WebSocket broadcaster.
    """
    is_recording: bool = False
    fps: float = 0.0
    total_frames: int = 0
    face_count: int = 0
    emotion_counts: Dict[str, int] = field(default_factory=lambda: {
        "angry": 0, "disgust": 0, "fear": 0, 
        "happy": 0, "sad": 0, "surprise": 0, "neutral": 0
    })
    dominant_emotion: str = "neutral"
    confidence: float = 0.0
    last_emotions: List[str] = field(default_factory=list)
    boxes: List[Tuple[int, int, int, int]] = field(default_factory=list)
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_recording": self.is_recording,
            "fps": self.fps,
            "total_frames": self.total_frames,
            "face_count": self.face_count,
            "emotion_counts": self.emotion_counts,
            "dominant_emotion": self.dominant_emotion,
            "confidence": self.confidence,
            "duration": self.duration,
        }


@dataclass
class AgentState:
    """
    Final analysis state from AgentService.
    Updated after processing is complete.
    """
    final_state: Optional[str] = None  # SATISFIED | NEUTRAL | DISSATISFIED
    confidence: Dict[str, float] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_state": self.final_state,
            "confidence": self.confidence,
            "result": self.result,
        }


@dataclass
class SessionState:
    """
    Complete session state - Single Source of Truth.
    All services update this, WebSocket reads from this.
    """
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    audio: AudioState = field(default_factory=AudioState)
    video: VideoState = field(default_factory=VideoState)
    agent: AgentState = field(default_factory=AgentState)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "audio": self.audio.to_dict(),
            "video": self.video.to_dict(),
            "agent": self.agent.to_dict(),
        }
