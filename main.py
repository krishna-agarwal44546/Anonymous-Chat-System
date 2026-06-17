import asyncio
import os
import logging
from http import HTTPStatus
from websockets.asyncio.server import ServerConnection, serve
from websockets.http11 import Response

# --- SILENCE RENDER'S HEALTH CHECK LOGS ---
logging.getLogger("websockets.server").setLevel(logging.CRITICAL)

PORT = int(os.environ.get("PORT", 10000))

# Keep track of connected browser interfaces
connected_browsers = set()

# Minimalist HTML page that connects via native browser WebSockets
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Live Monitor</title>
    <style>
        body { font-family: sans-serif; margin: 40px; background: #1e1e2e; color: #cdd6f4; }
        h1 { color: #89b4fa; }
        #log { background: #313244; padding: 20px; border-radius: 8px; font-family: monospace; height: 400px; overflow-y: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .msg { padding: 6px 0; border-bottom: 1px solid #45475a; color: #a6e3a1; }
        .status { color: #f9e2af; font-style: italic; }
    </style>
</head>
<body>
    <h1>Live Server Message Monitor</h1>
    <div id="log"><div class="status">Connecting to WebSocket server...</div></div>

    <script>
        // Automatically determine the correct WebSocket protocol (ws:// or wss://)
        const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        const socket = new WebSocket(wsProtocol + window.location.host);

        const logDiv = document.getElementById('log');

        socket.onopen = () => {
            logDiv.innerHTML = '<div class="status">Connected! Awaiting console client messages...</div>';
        };

        socket.onmessage = (event) => {
            const p = document.createElement('div');
            p.className = 'msg';
            p.innerText = `[${new Date().toLocaleTimeString()}] ${event.data}`;
            logDiv.appendChild(p);
            logDiv.scrollTop = logDiv.scrollHeight; 
        };

        socket.onclose = () => {
            const p = document.createElement('div');
            p.className = 'status';
            p.innerText = 'Connection lost. Refresh to reconnect.';
            logDiv.appendChild(p);
        };
    </script>
</body>
</html>
"""

async def handle_communication(websocket):
    """
    Handles both incoming console clients AND browser monitors.
    """
    # Detect if the connection is a browser identifying itself via its User-Agent
    headers = dict(websocket.request_headers)
    user_agent = headers.get("user-agent", "")
    is_browser = "Mozilla" in user_agent or "Chrome" in user_agent or "Safari" in user_agent

    if is_browser:
        # Register the browser tab to receive broadcasts
        connected_browsers.add(websocket)
        print("Web UI Monitor connected.")
        try:
            # Keep connection open indefinitely waiting for close signal
            async for _ in websocket:
                pass 
        finally:
            connected_browsers.remove(websocket)
            print("Web UI Monitor disconnected.")
    else:
        # It's a Python console client!
        print("Python console client connected.")
        try:
            async for message in websocket:
                print(f"Received from console: {message}")
                
                # 1. Echo back to the sending python console client
                await websocket.send(f"Echo: {message}")
                
                # 2. Broadcast it to all open web browser monitoring pages
                if connected_browsers:
                    # Create transmission tasks for every active browser window
                    broadcast_tasks = [
                        asyncio.create_task(browser.send(f"Client sent: {message}"))
                        for browser in connected_browsers
                    ]
                    await asyncio.gather(*broadcast_tasks, return_exceptions=True)
                    
        except Exception as e:
            print(f"Console client session ended: {e}")

class RenderServerConnection(ServerConnection):
    def respond_to_invalid_request(self, exception):
        """
        1. Bypasses Render health checks gracefully.
        2. Serves our UI HTML file directly when someone visits the URL in a browser.
        """
        # Catch standard browser HTTP page loads (which fail the WS upgrade handshake initial parsing)
        if exception.__cause__ and "got GET" in str(exception.__cause__):
            return Response(
                status_code=HTTPStatus.OK,
                reason_phrase="OK",
                headers=[("Content-Type", "text/html")],
                body=HTML_PAGE.encode("utf-8")
            )
            
        # Catch Render's automated HEAD health checks
        if exception.__cause__ and "got HEAD" in str(exception.__cause__):
            return Response(
                status_code=HTTPStatus.OK,
                reason_phrase="OK",
                headers=[],
                body=b""
            )
            
        return super().respond_to_invalid_request(exception)

async def main():
    async with serve(
        handle_communication,
        "0.0.0.0",
        PORT,
        create_connection=RenderServerConnection
    ):
        print(f"WebSockets Server running on port {PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())