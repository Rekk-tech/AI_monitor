"""Test WebSocket connection"""
import asyncio
import websockets
import json


async def test_websocket():
    """Test WebSocket connection to backend"""
    uri = "ws://localhost:8000/ws/session/test-session"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as ws:
            # Receive connection confirmation
            response = await ws.recv()
            data = json.loads(response)
            print(f"Received: {json.dumps(data, indent=2)}")
            
            # Send heartbeat
            await ws.send(json.dumps({"type": "heartbeat"}))
            print("Sent heartbeat")
            
            # Wait for any response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Response: {response}")
            except asyncio.TimeoutError:
                print("No immediate response (expected for heartbeat)")
            
            print("\n✅ WebSocket connection successful!")
            return True
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_websocket())
