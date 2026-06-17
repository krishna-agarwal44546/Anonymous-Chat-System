import asyncio
import os
import websockets

PORT = int(os.environ.get("PORT", 8765))

async def echo(websocket):
    async for message in websocket:
        print(f"Received: {message}")
        await websocket.send(f"Echo: {message}")

async def main():
    async with websockets.serve(
        echo,
        "0.0.0.0",
        PORT
    ):
        print(f"WebSocket server running on port {PORT}")
        await asyncio.Future()  # run forever

asyncio.run(main())