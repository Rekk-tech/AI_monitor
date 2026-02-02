"""
Event Broadcaster Service
Provides singleton access to broadcast events to WebSocket clients.
Includes throttled broadcast functions for high-frequency data.
"""

from typing import Any, Dict, Optional
import asyncio
import time

# CRITICAL: Import the SHARED connection_manager singleton, not create a new one!
from app.services.websocket_manager import connection_manager, ConnectionManager
from app.domain.ws_events import (
    create_video_stats_event,
    create_audio_metrics_event,
    create_audio_status_event,
    create_session_state_event,
    create_session_completed_event,
    create_final_result_event,
    create_error_event,
)
from app.utils.throttle import audio_throttle, video_throttle


def get_connection_manager() -> ConnectionManager:
    """Get the singleton connection manager instance"""
    # Return the SHARED instance from websocket_manager.py
    return connection_manager


class EventBroadcaster:
    """
    Service for broadcasting events to WebSocket clients.
    Provides throttled and non-throttled methods for different event types.
    """

    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    # ================================
    # Video Events (Throttled 200ms)
    # ================================

    async def broadcast_video_stats(
        self,
        session_id: str,
        face_count: int = 0,
        dominant_emotion: str = "neutral",
        confidence: float = 0.0,
        total_frames: int = 0,
        emotion_counts: Dict[str, int] = None,
        duration: float = 0.0,
    ):
        """Broadcast video stats to WebSocket clients"""
        # Note: Throttling is done in schedule_broadcast_video_stats
        
        event = create_video_stats_event(
            session_id=session_id,
            face_count=face_count,
            dominant_emotion=dominant_emotion,
            confidence=confidence,
            total_frames=total_frames,
            emotion_counts=emotion_counts,
            duration=duration,
        )
        await self.manager.broadcast_to_session(session_id, event)

    # ================================
    # Audio Events (Throttled 100ms)
    # ================================

    async def broadcast_audio_metrics(
        self,
        session_id: str,
        amplitude: float = 0.0,
        is_speech: bool = False,
        duration: float = 0.0,
        total_frames: int = 0,
        speech_frames: int = 0,
    ):
        """Broadcast audio metrics (throttled at 100ms)"""
        if not audio_throttle.should_execute(f"audio_{session_id}"):
            return
        
        event = create_audio_metrics_event(
            session_id=session_id,
            amplitude=amplitude,
            is_speech=is_speech,
            duration=duration,
            total_frames=total_frames,
            speech_frames=speech_frames,
        )
        await self.manager.broadcast_to_session(session_id, event)

    async def broadcast_audio_status(
        self,
        session_id: str,
        status: str,
        file_path: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Broadcast audio status change (not throttled)"""
        event = create_audio_status_event(
            session_id=session_id,
            status=status,
            file_path=file_path,
            error=error,
        )
        await self.manager.broadcast_to_session(session_id, event)

    # ================================
    # Session Events (Not Throttled)
    # ================================

    async def broadcast_session_state(
        self,
        session_id: str,
        video_active: bool = False,
        audio_active: bool = False,
        status: str = "idle",
    ):
        """Broadcast session state changes"""
        event = create_session_state_event(
            session_id=session_id,
            video_active=video_active,
            audio_active=audio_active,
            status=status,
        )
        await self.manager.broadcast_to_session(session_id, event)

    async def broadcast_session_completed(
        self,
        session_id: str,
        video_summary: Dict[str, Any] = None,
        audio_summary: Dict[str, Any] = None,
    ):
        """Broadcast session completed event"""
        event = create_session_completed_event(
            session_id=session_id,
            video_summary=video_summary,
            audio_summary=audio_summary,
        )
        await self.manager.broadcast_to_session(session_id, event)

    # ================================
    # Agent Events (Not Throttled)
    # ================================

    async def broadcast_final_result(
        self,
        session_id: str,
        final_state: str,
        confidence: Dict[str, float] = None,
        reasoning: list = None,
        recommendation: str = "",
    ):
        """Broadcast final agent analysis result"""
        event = create_final_result_event(
            session_id=session_id,
            final_state=final_state,
            confidence=confidence,
            reasoning=reasoning,
            recommendation=recommendation,
        )
        await self.manager.broadcast_to_session(session_id, event)

    # ================================
    # Error Events (Not Throttled)
    # ================================

    async def broadcast_error(
        self,
        session_id: str,
        message: str,
        code: Optional[str] = None,
    ):
        """Broadcast error to session clients"""
        event = create_error_event(
            session_id=session_id,
            message=message,
            code=code,
        )
        await self.manager.broadcast_to_session(session_id, event)


# Singleton broadcaster instance
_event_broadcaster: Optional[EventBroadcaster] = None


def get_event_broadcaster() -> EventBroadcaster:
    """Get the singleton event broadcaster instance"""
    global _event_broadcaster
    if _event_broadcaster is None:
        _event_broadcaster = EventBroadcaster(get_connection_manager())
    return _event_broadcaster


# ================================
# Sync-Safe Broadcast Functions
# (For use in sync contexts like callbacks)
# ================================

# Store reference to the main event loop
_main_loop = None

def set_main_loop(loop):
    """Set the main event loop reference (call from FastAPI startup)"""
    global _main_loop
    _main_loop = loop
    print(f"[BROADCAST] Main loop set: {loop}")


def schedule_broadcast_video_stats(session_id: str, **kwargs):
    """Schedule video stats broadcast from sync context (thread-safe)"""
    global _main_loop
    import asyncio  # Import at function level
    
    if not video_throttle.should_execute(f"schedule_video_{session_id}"):
        return
    
    broadcaster = get_event_broadcaster()
    face_count = kwargs.get('face_count', 0)
    
    print(f"[SCHEDULE] Scheduling broadcast for session={session_id}, faces={face_count}, main_loop={_main_loop is not None}")
    
    async def _broadcast():
        # Debug log
        clients = len(broadcaster.manager.active_connections.get(session_id, set()))
        print(f"[BROADCAST] video_stats to session={session_id}, clients={clients}, faces={face_count}")
        await broadcaster.broadcast_video_stats(session_id, **kwargs)
    
    # Use the stored main loop for thread-safe scheduling
    if _main_loop and _main_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(_broadcast(), _main_loop)
        print(f"[SCHEDULE] Future scheduled: {future}")
    else:
        # Fallback: try current loop
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(_broadcast())
        except RuntimeError:
            print(f"[BROADCAST] WARNING: No event loop available for session {session_id}, main_loop={_main_loop}")


def schedule_broadcast_audio_metrics(session_id: str, **kwargs):
    """Schedule audio metrics broadcast from sync context (thread-safe)"""
    global _main_loop
    import asyncio
    
    if not audio_throttle.should_execute(f"audio_{session_id}"):
        return
    
    broadcaster = get_event_broadcaster()
    speech_frames = kwargs.get('speech_frames', 0)
    total_frames = kwargs.get('total_frames', 1)
    
    async def _broadcast():
        clients = len(broadcaster.manager.active_connections.get(session_id, set()))
        print(f"[BROADCAST] audio_metrics to session={session_id}, clients={clients}, speech_frames={speech_frames}/{total_frames}")
        await broadcaster.broadcast_audio_metrics(session_id, **kwargs)
    
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(_broadcast(), _main_loop)
    else:
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(_broadcast())
        except RuntimeError:
            print(f"[BROADCAST] WARNING: No event loop for audio metrics - session {session_id}")


def schedule_broadcast_audio_status(session_id: str, **kwargs):
    """Schedule audio status broadcast from sync context (thread-safe)"""
    global _main_loop
    import asyncio
    
    broadcaster = get_event_broadcaster()
    
    async def _broadcast():
        await broadcaster.broadcast_audio_status(session_id, **kwargs)
    
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(_broadcast(), _main_loop)
    else:
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(_broadcast())
        except RuntimeError:
            pass


def schedule_broadcast_final_result(session_id: str, **kwargs):
    """Schedule final result broadcast from sync context (thread-safe)"""
    global _main_loop
    import asyncio
    
    broadcaster = get_event_broadcaster()
    
    async def _broadcast():
        clients = len(broadcaster.manager.active_connections.get(session_id, set()))
        print(f"[BROADCAST] final_result to session={session_id}, clients={clients}")
        await broadcaster.broadcast_final_result(session_id, **kwargs)
    
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(_broadcast(), _main_loop)
    else:
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(_broadcast())
        except RuntimeError:
            pass
