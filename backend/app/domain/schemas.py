from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Union, Literal
from .enums import SatisfactionState, Sentiment

class FaceEmotionResult(BaseModel):
    emotion: str
    confidence: float
    timestamp: float

class AudioInternalEmotion(BaseModel):
    label: str
    score: float

class AudioAnalysisResult(BaseModel):
    emotions: List[AudioInternalEmotion]
    dominant_sentiment: Sentiment
    satisfied_score: float
    dissatisfied_score: float

class SessionResult(BaseModel):
    final_state: SatisfactionState
    confidence: Dict[str, float]
    image_summary: Dict[str, Union[str, float, Dict]]
    audio_summary: Dict[str, Union[str, float]]
    reasoning: List[str] = []
    recommendation: str

# =========================
# AUDIO API SCHEMAS
# =========================

# Audio session status type
AudioStatus = Literal["recording", "processing", "done", "error", "idle"]

# Request schemas
class StartRecordRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Unique session identifier")

class StopRecordRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Session ID to stop")

# Response schemas
class StartRecordResponse(BaseModel):
    status: Literal["recording_started"]
    session_id: str

class StopRecordResponse(BaseModel):
    status: Literal["recording_stopped"]
    session_id: str
    file: str

class LiveMetricsResponse(BaseModel):
    amplitude: float = Field(..., ge=0.0, le=1.0, description="Current audio amplitude (0-1)")
    is_speech: bool = Field(..., description="Whether speech is detected")
    duration: float = Field(..., ge=0.0, description="Recording duration in seconds")

class StatusResponse(BaseModel):
    status: AudioStatus

class AudioProcessingResult(BaseModel):
    satisfied: float = Field(..., ge=0.0, le=1.0)
    dissatisfied: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    note: Optional[str] = None

class LatestResultResponse(BaseModel):
    status: AudioStatus
    result: Optional[AudioProcessingResult] = None
    error: Optional[str] = None

# Internal store schema (for documentation)
class AudioSessionStore(BaseModel):
    """Schema for audio_results_store entries"""
    status: AudioStatus
    file: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
