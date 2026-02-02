"""
WebSocket Router
Handles WebSocket connections for real-time session updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import connection_manager
from app.domain.ws_events import (
    create_connected_event,
    create_error_event,
)
import asyncio
import time

router = APIRouter()

# Heartbeat configuration
HEARTBEAT_INTERVAL = 5.0  # Send heartbeat every 5 seconds
CLIENT_TIMEOUT = 15.0     # Disconnect if no response in 15 seconds


@router.websocket("/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time session updates.
    
    Connect to receive:
    - Video stats updates
    - Audio metrics updates
    - Session state changes
    - Heartbeat (every 5 seconds)
    
    URL: ws://localhost:8000/ws/session/{session_id}
    """
    await connection_manager.connect(websocket, session_id)
    print(f"[WS] Client connected to session {session_id}")
    
    last_client_response = time.time()
    
    try:
        # Send connection confirmation
        await connection_manager.send_personal(
            websocket,
            create_connected_event(session_id)
        )
        
        # Start heartbeat + message handling loop
        while True:
            try:
                # Wait for client messages with short timeout for heartbeat
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=HEARTBEAT_INTERVAL
                )
                
                # Update last response time
                last_client_response = time.time()
                
                # Handle client messages
                msg_type = data.get("type", "")
                
                if msg_type == "ping":
                    # Respond to ping with pong
                    await connection_manager.send_personal(
                        websocket,
                        {
                            "type": "pong",
                            "session_id": session_id,
                            "timestamp": time.time()
                        }
                    )
                elif msg_type == "heartbeat":
                    # Client heartbeat acknowledged
                    pass
                else:
                    print(f"[WS] Received from {session_id}: {msg_type}")
                    
            except asyncio.TimeoutError:
                # Check if client is still alive
                time_since_response = time.time() - last_client_response
                
                if time_since_response > CLIENT_TIMEOUT:
                    print(f"[WS] Client {session_id} timed out (no response for {time_since_response:.1f}s)")
                    break
                
                # Send heartbeat to keep connection alive
                try:
                    await connection_manager.send_personal(
                        websocket,
                        {
                            "type": "heartbeat",
                            "session_id": session_id,
                            "timestamp": time.time(),
                            "server_time": time.time()
                        }
                    )
                except Exception as e:
                    print(f"[WS] Failed to send heartbeat to {session_id}: {e}")
                    break
                    
    except WebSocketDisconnect:
        print(f"[WS] Client disconnected from session {session_id}")
    except Exception as e:
        print(f"[WS] Error in session {session_id}: {e}")
        try:
            await connection_manager.send_personal(
                websocket,
                create_error_event(session_id, str(e))
            )
        except Exception:
            pass
    finally:
        connection_manager.disconnect(websocket, session_id)
        print(f"[WS] Session {session_id} cleanup complete")


@router.get("/sessions")
async def get_active_sessions():
    """Get list of active WebSocket sessions"""
    return {
        "sessions": connection_manager.get_connected_sessions(),
        "count": len(connection_manager.get_connected_sessions())
    }


@router.get("/health")
async def websocket_health():
    """WebSocket subsystem health check"""
    sessions = connection_manager.get_connected_sessions()
    return {
        "status": "healthy",
        "active_connections": len(sessions),
        "sessions": sessions,
        "heartbeat_interval_sec": HEARTBEAT_INTERVAL,
        "client_timeout_sec": CLIENT_TIMEOUT
    }

