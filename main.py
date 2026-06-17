import asyncio
import os
import websockets

PORT = int(os.environ.get("PORT", 10000))

async def echo(websocket):
    print("Client connected")

    async for message in websocket:
        print("Received:", message)
        await websocket.send(f"Echo: {message}")

async def main():
    async with websockets.serve(
        echo,
        "0.0.0.0",
        PORT
    ):
        print(f"WebSocket server running on port {PORT}")
        await asyncio.Future()

asyncio.run(main())