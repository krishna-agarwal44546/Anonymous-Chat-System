import asyncio
import os
import websockets
from http import HTTPStatus

PORT = int(os.environ.get("PORT", 10000))

async def echo(websocket):
    print("Client connected")

    async for message in websocket:
        print("Received:", message)
        await websocket.send(f"Echo: {message}")

# IMPORTANT: handle Render HTTP probes
async def process_request(path, request_headers):
    return HTTPStatus.OK, [], b"OK"

async def main():
    async with websockets.serve(
        echo,
        "0.0.0.0",
        PORT,
        process_request=process_request
    ):
        print(f"Server running on {PORT}")
        await asyncio.Future()

asyncio.run(main())