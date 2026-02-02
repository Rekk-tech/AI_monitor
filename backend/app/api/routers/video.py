from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from app.dependencies import video_service
from app.services.webrtc_service import get_webrtc_service
import cv2
import numpy as np

router = APIRouter()

# Pre-generate a black placeholder image for when camera is not ready
_placeholder_frame = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.putText(_placeholder_frame, "Waiting for camera...", (180, 250), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)
_, _placeholder_jpeg = cv2.imencode(".jpg", _placeholder_frame)
PLACEHOLDER_JPEG = _placeholder_jpeg.tobytes()


# ========================
# WebRTC Models
# ========================

class SDPOffer(BaseModel):
    sdp: str
    type: str
    session_id: str

class ICECandidate(BaseModel):
    candidate: str
    sdpMid: str
    sdpMLineIndex: int
    session_id: str


# ========================
# WebRTC Endpoints
# ========================

@router.post("/webrtc/offer")
async def webrtc_offer(offer: SDPOffer):
    """
    Handle WebRTC SDP offer from client.
    Returns SDP answer for peer connection.
    """
    try:
        webrtc = get_webrtc_service()
        
        # Set up frame callback to send to video pipeline
        def on_frame(frame):
            video_service.pipeline.enqueue(frame)
        
        webrtc.set_frame_callback(on_frame, offer.session_id)
        
        answer = await webrtc.create_offer(
            session_id=offer.session_id,
            sdp=offer.sdp,
            sdp_type=offer.type
        )
        return answer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webrtc/ice")
async def webrtc_ice(candidate: ICECandidate):
    """Add ICE candidate from client."""
    webrtc = get_webrtc_service()
    success = await webrtc.add_ice_candidate(
        session_id=candidate.session_id,
        candidate={
            "candidate": candidate.candidate,
            "sdpMid": candidate.sdpMid,
            "sdpMLineIndex": candidate.sdpMLineIndex
        }
    )
    return {"success": success}


@router.post("/webrtc/close")
async def webrtc_close(session_id: str = Query(...)):
    """Close WebRTC connection for session."""
    webrtc = get_webrtc_service()
    await webrtc.close_connection(session_id)
    return {"status": "closed"}


# ========================
# Legacy HTTP Endpoints
# ========================

@router.post("/start")
def start_video(session_id: str = Query(None, description="Session ID to use for WebSocket sync")):
    video_service.start_session(session_id=session_id)
    return {"status": "started", "session_id": session_id}

@router.post("/stop")
def stop_video():
    stats = video_service.stop_session()
    return {"status": "stopped", "stats": stats if stats else {}}

@router.get("/frame")
def get_video_frame():
    """
    Returns the latest processed frame as JPEG.
    Used for realtime polling by the dashboard (legacy).
    """
    frame = video_service.get_frame()
    if frame is None:
        # Return placeholder instead of 204 to prevent img onError
        return Response(content=PLACEHOLDER_JPEG, media_type="image/jpeg")
        
    # Encode to JPEG
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        return Response(content=PLACEHOLDER_JPEG, media_type="image/jpeg")
        
    return Response(content=buffer.tobytes(), media_type="image/jpeg")
