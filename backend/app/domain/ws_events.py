"""
WebSocket Event Types and Schemas
Defines the event structure for real-time updates.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class EventType(str, Enum):
    """Types of real-time events"""
    
    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    
    # Video events
    VIDEO_STATS = "video_stats"
    
    # Audio events
    AUDIO_METRICS = "audio_metrics"
    AUDIO_STATUS = "audio_status"
    
    # Session events
    SESSION_STATE = "session_state"
    SESSION_COMPLETED = "session_completed"
    
    # Agent events
    FINAL_RESULT = "final_result"


class WSEvent(BaseModel):
    """Base WebSocket event schema"""
    
    type: EventType
    session_id: str
    timestamp: str = ""
    data: Dict[str, Any] = {}
    
    def __init__(self, **kwargs):
        if not kwargs.get("timestamp"):
            kwargs["timestamp"] = datetime.now().isoformat()
        super().__init__(**kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }


# ===========================
# Event Factory Functions
# ===========================

def create_connected_event(session_id: str) -> Dict[str, Any]:
    """Create connection success event"""
    return WSEvent(
        type=EventType.CONNECTED,
        session_id=session_id,
        data={"message": "Connected to session"}
    ).to_dict()


def create_video_stats_event(
    session_id: str,
    face_count: int = 0,
    dominant_emotion: str = "neutral",
    confidence: float = 0.0,
    total_frames: int = 0,
    emotion_counts: Dict[str, int] = None,
    duration: float = 0.0,
) -> Dict[str, Any]:
    """Create video stats update event"""
    return WSEvent(
        type=EventType.VIDEO_STATS,
        session_id=session_id,
        data={
            "face_count": face_count,
            "dominant_emotion": dominant_emotion,
            "confidence": round(confidence, 3),
            "total_frames": total_frames,
            "emotion_counts": emotion_counts or {},
            "duration": round(duration, 2),
        }
    ).to_dict()


def create_audio_metrics_event(
    session_id: str,
    amplitude: float = 0.0,
    is_speech: bool = False,
    duration: float = 0.0,
    total_frames: int = 0,
    speech_frames: int = 0,
) -> Dict[str, Any]:
    """Create audio metrics update event"""
    return WSEvent(
        type=EventType.AUDIO_METRICS,
        session_id=session_id,
        data={
            "amplitude": round(amplitude, 3),
            "is_speech": is_speech,
            "duration": round(duration, 2),
            "total_frames": total_frames,
            "speech_frames": speech_frames,
        }
    ).to_dict()


def create_audio_status_event(
    session_id: str,
    status: str,
    file_path: Optional[str] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Create audio status change event"""
    return WSEvent(
        type=EventType.AUDIO_STATUS,
        session_id=session_id,
        data={
            "status": status,
            "file_path": file_path,
            "error": error,
        }
    ).to_dict()


def create_session_state_event(
    session_id: str,
    video_active: bool = False,
    audio_active: bool = False,
    status: str = "idle",
) -> Dict[str, Any]:
    """Create session state update event"""
    return WSEvent(
        type=EventType.SESSION_STATE,
        session_id=session_id,
        data={
            "video_active": video_active,
            "audio_active": audio_active,
            "status": status,
        }
    ).to_dict()


def create_session_completed_event(
    session_id: str,
    video_summary: Dict[str, Any] = None,
    audio_summary: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Create session completed event"""
    return WSEvent(
        type=EventType.SESSION_COMPLETED,
        session_id=session_id,
        data={
            "video_summary": video_summary or {},
            "audio_summary": audio_summary or {},
        }
    ).to_dict()


def create_final_result_event(
    session_id: str,
    final_state: str,
    confidence: Dict[str, float] = None,
    reasoning: list = None,
    recommendation: str = "",
) -> Dict[str, Any]:
    """Create final result event from agent analysis"""
    return WSEvent(
        type=EventType.FINAL_RESULT,
        session_id=session_id,
        data={
            "final_state": final_state,
            "confidence": confidence or {},
            "reasoning": reasoning or [],
            "recommendation": recommendation,
        }
    ).to_dict()


def create_error_event(
    session_id: str,
    message: str,
    code: Optional[str] = None,
) -> Dict[str, Any]:
    """Create error event"""
    return WSEvent(
        type=EventType.ERROR,
        session_id=session_id,
        data={
            "message": message,
            "code": code,
        }
    ).to_dict()
