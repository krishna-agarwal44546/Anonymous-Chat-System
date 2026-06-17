import asyncio
import os
from http import HTTPStatus
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import InvalidMessage

PORT = int(os.environ.get("PORT", 10000))

async def echo(websocket):
    print("Client connected")
    async for message in websocket:
        print("Received:", message)
        await websocket.send(f"Echo: {message}")

class RenderServerConnection(ServerConnection):
    async def handshake(self, *args, **kwargs):
        try:
            return await super().handshake(*args, **kwargs)
        except InvalidMessage as exc:
            # Check if the failure was due to Render's HEAD health check
            if "unsupported HTTP method; expected GET; got HEAD" in str(exc.__cause__):
                # Respond with a clean HTTP 200 OK to Render's probe
                self.transport.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
                self.transport.close()
                # Suppress the exception so your logs stay clean
                raise asyncio.CancelledError()
            raise exc

async def main():
    # Use create_connection to inject our custom connection handler
    async with serve(
        echo,
        "0.0.0.0",
        PORT,
        create_connection=RenderServerConnection
    ):
        print(f"Server running on port {PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())