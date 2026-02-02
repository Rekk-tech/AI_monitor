from app.services.video_service import VideoService
from app.services.audio_service import AudioService
from app.services.agent_service import AgentService
from app.services.speech_emotion_service import SpeechEmotionService
from app.pipelines.audio_pipeline import AudioPipeline

# =========================
# GLOBAL SINGLETON OBJECTS
# =========================

video_service = VideoService()
audio_service = AudioService()

# 🔥 LOAD MODEL 1 LẦN DUY NHẤT
speech_emotion_service = SpeechEmotionService()

# 🔁 Inject model vào pipeline
audio_pipeline = AudioPipeline(speech_emotion_service)

agent_service = AgentService()

# =========================
# AUDIO RESULTS STORE
# =========================
# In-memory store for audio session results
# Schema per session:
# {
#   session_id: {
#     "status": "recording" | "processing" | "done" | "error",
#     "file": str | None,
#     "result": dict | None,
#     "error": str | None
#   }
# }
audio_results_store = {}

def create_audio_session(session_id: str) -> dict:
    """Create a new audio session with proper structure"""
    session = {
        "status": "recording",
        "file": None,
        "result": None,
        "error": None
    }
    audio_results_store[session_id] = session
    return session
