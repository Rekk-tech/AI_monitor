"""
WebSocket Connection Manager
Manages WebSocket connections for real-time session updates.
"""

from fastapi import WebSocket
import asyncio
from typing import Dict, Set, Any
from datetime import datetime
import json


class ConnectionManager:
    """
    Manages WebSocket connections per session.
    Each session can have multiple connected clients.
    """
    
    def __init__(self):
        # session_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # session_id -> session state
        self.session_states: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept connection and add to session group"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        
        # Initialize session state if not exists
        if session_id not in self.session_states:
            self.session_states[session_id] = {
                "connected_at": datetime.now().isoformat(),
                "client_count": 0,
            }
        
        self.session_states[session_id]["client_count"] = len(
            self.active_connections[session_id]
        )
        
        print(f"[WS] Client connected to session {session_id}. "
              f"Total clients: {self.session_states[session_id]['client_count']}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove connection from session group"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            if session_id in self.session_states:
                self.session_states[session_id]["client_count"] = len(
                    self.active_connections[session_id]
                )
            
            # Clean up empty sessions
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                if session_id in self.session_states:
                    del self.session_states[session_id]
                print(f"[WS] Session {session_id} closed (no clients)")
            else:
                print(f"[WS] Client disconnected from session {session_id}")
    
    async def send_personal(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send message to a specific client"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            print(f"[WS] Failed to send personal message: {e}")
    
    async def broadcast_to_session(self, session_id: str, data: Dict[str, Any]):
        """Broadcast message to all clients in a session"""
        if session_id not in self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections[session_id]:
            try:
                await connection.send_json(data)
            except Exception as e:
                print(f"[WS] Client disconnected during broadcast: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, session_id)
    
    async def broadcast_all(self, data: Dict[str, Any]):
        """Broadcast message to all sessions"""
        for session_id in list(self.active_connections.keys()):
            await self.broadcast_to_session(session_id, data)
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session state info"""
        return self.session_states.get(session_id, {})
    
    def get_connected_sessions(self) -> list:
        """Get list of active session IDs"""
        return list(self.active_connections.keys())
    
    def is_session_connected(self, session_id: str) -> bool:
        """Check if session has any connected clients"""
        return session_id in self.active_connections and len(
            self.active_connections[session_id]
        ) > 0


# Global connection manager instance
connection_manager = ConnectionManager()
