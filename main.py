import asyncio
import os
from http import HTTPStatus
import websockets

PORT = int(os.environ.get("PORT", 8765))

async def echo(websocket):
    async for message in websocket:
        print(f"Received: {message}")
        await websocket.send(f"Echo: {message}")

def process_request(connection, request):
    return connection.respond(
        HTTPStatus.OK,
        "WebSocket server is running\n"
    )

async def main():
    async with websockets.serve(
        echo,
        "0.0.0.0",
        PORT,
        process_request=process_request
    ):
        print(f"WebSocket server running on port {PORT}")
        await asyncio.Future()

asyncio.run(main())