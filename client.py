import asyncio
import websockets

async def communicate():
    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as websocket:
        while True:
            await websocket.send(input("Enter a message to send: "))

asyncio.run(communicate())

