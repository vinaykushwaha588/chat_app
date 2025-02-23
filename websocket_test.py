import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/chat/general/"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"message": "Hello from WebSocket!"}))
        response = await websocket.recv()
        print("Received:", response)
asyncio.run(test_websocket())
