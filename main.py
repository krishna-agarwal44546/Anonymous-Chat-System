import asyncio
import os
from http import HTTPStatus
from websockets.asyncio.server import ServerConnection, serve
from websockets.http11 import Response

PORT = int(os.environ.get("PORT", 10000))

async def echo(websocket):
    print("Client connected")
    async for message in websocket:
        print("Received:", message)
        await websocket.send(f"Echo: {message}")

class RenderServerConnection(ServerConnection):
    def respond_to_invalid_request(self, exception):
        """
        Intercepts requests that fail the WebSocket handshake (like Render's health checks)
        and returns a standard HTTP response.
        """
        # If Render sends a HEAD request, the underlying cause will mention 'got HEAD'
        if exception.__cause__ and "got HEAD" in str(exception.__cause__):
            # Return a valid HTTP response cleanly. Websockets handles the transport closure.
            return Response(
                status_code=HTTPStatus.OK,
                reason_phrase="OK",
                headers=[],
                body=b""  # HEAD requests must have an empty body
            )
        
        # Fallback to default library behavior for genuine bad requests
        return super().respond_to_invalid_request(exception)

async def main():
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