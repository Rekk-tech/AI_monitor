"""
WebRTC Signaling Service for real-time video streaming.
Uses aiortc for WebRTC handling and integrates with AI pipeline.
"""

import asyncio
import logging
from typing import Optional, Callable
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaRelay
import av
import numpy as np

logger = logging.getLogger(__name__)


class VideoFrameProcessor:
    """Extracts frames from WebRTC video track for AI processing."""
    
    def __init__(self, on_frame: Callable[[np.ndarray], None]):
        self.on_frame = on_frame
        self._running = False
    
    async def process_track(self, track: MediaStreamTrack):
        """Process incoming video frames from WebRTC track."""
        self._running = True
        frame_count = 0
        
        try:
            while self._running:
                try:
                    frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                    frame_count += 1
                    
                    # Convert to numpy array (BGR for OpenCV compatibility)
                    img = frame.to_ndarray(format="bgr24")
                    
                    # Call the frame handler (throttled in pipeline)
                    if self.on_frame:
                        self.on_frame(img)
                        
                except asyncio.TimeoutError:
                    logger.warning("Frame receive timeout")
                    continue
                except Exception as e:
                    logger.error(f"Frame processing error: {e}")
                    break
                    
        finally:
            logger.info(f"Video track ended, processed {frame_count} frames")
    
    def stop(self):
        self._running = False


class WebRTCService:
    """
    WebRTC signaling and connection management.
    Handles SDP exchange and ICE candidates.
    """
    
    def __init__(self):
        self.peer_connections: dict[str, RTCPeerConnection] = {}
        self.frame_processors: dict[str, VideoFrameProcessor] = {}
        self.relay = MediaRelay()
        self._on_frame_callback: Optional[Callable] = None
        self._session_id: Optional[str] = None
    
    def set_frame_callback(self, callback: Callable[[np.ndarray], None], session_id: str):
        """Set callback for processing video frames."""
        self._on_frame_callback = callback
        self._session_id = session_id
    
    async def create_offer(self, session_id: str, sdp: str, sdp_type: str) -> dict:
        """
        Handle SDP offer from client and return answer.
        
        Args:
            session_id: Unique session identifier
            sdp: SDP offer from client
            sdp_type: Type of SDP (usually 'offer')
            
        Returns:
            dict with SDP answer
        """
        # Create peer connection
        pc = RTCPeerConnection()
        self.peer_connections[session_id] = pc
        
        # Track connection state
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state: {pc.connectionState}")
            if pc.connectionState == "failed":
                await self.close_connection(session_id)
        
        @pc.on("track")
        def on_track(track):
            logger.info(f"Received track: {track.kind}")
            
            if track.kind == "video":
                # Create frame processor
                processor = VideoFrameProcessor(self._on_frame_callback)
                self.frame_processors[session_id] = processor
                
                # Start processing in background
                asyncio.create_task(processor.process_track(track))
        
        # Set remote description (client's offer)
        offer = RTCSessionDescription(sdp=sdp, type=sdp_type)
        await pc.setRemoteDescription(offer)
        
        # Create and set local description (our answer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        logger.info(f"WebRTC connection established for session {session_id}")
        
        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }
    
    async def add_ice_candidate(self, session_id: str, candidate: dict) -> bool:
        """Add ICE candidate from client."""
        pc = self.peer_connections.get(session_id)
        if not pc:
            logger.warning(f"No peer connection for session {session_id}")
            return False
        
        try:
            from aiortc import RTCIceCandidate
            
            # Parse candidate string
            ice_candidate = RTCIceCandidate(
                sdpMid=candidate.get("sdpMid"),
                sdpMLineIndex=candidate.get("sdpMLineIndex"),
                candidate=candidate.get("candidate")
            )
            await pc.addIceCandidate(ice_candidate)
            return True
        except Exception as e:
            logger.error(f"Failed to add ICE candidate: {e}")
            return False
    
    async def close_connection(self, session_id: str):
        """Close WebRTC connection for session."""
        # Stop frame processor
        processor = self.frame_processors.pop(session_id, None)
        if processor:
            processor.stop()
        
        # Close peer connection
        pc = self.peer_connections.pop(session_id, None)
        if pc:
            await pc.close()
            logger.info(f"WebRTC connection closed for session {session_id}")
    
    async def close_all(self):
        """Close all connections (for shutdown)."""
        for session_id in list(self.peer_connections.keys()):
            await self.close_connection(session_id)


# Singleton instance
_webrtc_service: Optional[WebRTCService] = None


def get_webrtc_service() -> WebRTCService:
    """Get or create WebRTC service singleton."""
    global _webrtc_service
    if _webrtc_service is None:
        _webrtc_service = WebRTCService()
    return _webrtc_service
