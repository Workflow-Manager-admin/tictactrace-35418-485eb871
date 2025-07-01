import threading
import asyncio
from typing import Dict, Set, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from .database import init_db
from .user import router as user_router
from .game import router as game_router

app = FastAPI(
    title="Tic Tac Toe Backend API",
    description="""
API backend for Tic Tac Toe fullstack app. Features: create/join games, submit moves, track state and results, user management.

**WebSocket API:**  
Real-time move and board updates are available over a WebSocket connection at `/ws/games/{game_id}`.  
See the `/ws/docs` endpoint for usage instructions and message format.
""",
    version="1.0.0",
    openapi_tags=[
        {"name": "games", "description": "Tic Tac Toe game session and move endpoints."},
        {"name": "users", "description": "User registration and demo login endpoints."},
        {"name": "websocket", "description": "WebSocket endpoints for real-time game updates."}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """
    PUBLIC_INTERFACE
    Initialize the database at startup.
    """
    init_db()

# -- Real-Time WebSocket Hub --
class GameConnectionManager:
    """
    PUBLIC_INTERFACE
    Manages WebSocket connections for real-time board/move push updates for each game.
    Maintains connections per game_id for efficient broadcasting.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    # PUBLIC_INTERFACE
    def connect(self, game_id: int, websocket: WebSocket):
        """Accepts WebSocket and adds it to the game's connection pool."""
        websocket.accept()
        with self.lock:
            self.active_connections.setdefault(game_id, set()).add(websocket)

    # PUBLIC_INTERFACE
    def disconnect(self, game_id: int, websocket: WebSocket):
        """Removes WebSocket from the game's pool on disconnect."""
        with self.lock:
            conns = self.active_connections.get(game_id, set())
            conns.discard(websocket)
            if not conns:
                self.active_connections.pop(game_id, None)

    # PUBLIC_INTERFACE
    async def broadcast(self, game_id: int, message: dict):
        """Send message (board/move update) to all clients in the game."""
        with self.lock:
            websockets = list(self.active_connections.get(game_id, set()))
        for ws in websockets:
            try:
                await ws.send_json(message)
            except Exception:
                # Remove broken connection
                self.disconnect(game_id, ws)

# Global connection manager instance
ws_manager = GameConnectionManager()

# -- WebSocket Endpoint --
@app.websocket("/ws/games/{game_id}")
async def websocket_game_board(websocket: WebSocket, game_id: int):
    """
    PUBLIC_INTERFACE
    WebSocket endpoint for subscribing to real-time board/move updates for a single game.

    - **Path:** `/ws/games/{game_id}`
    - **Description:** Join to receive push notifications whenever the board or a move changes in the given game.
    - **Message format:** JSON object with at least fields: `event` ("move", "game_end", etc), and relevant data (board, move, etc).
    - **Tags:** websocket, games

    Usage:
    - Connect to ws://<server>/ws/games/{game_id}
    - The server will push an event after each move (by any player), or when game finishes.
    - Messages:
        ```json
        {
            "event": "move",
            "game_id": 1,
            "board": "XO---X---",
            "move": {"position": 4, "symbol": "O", "player_id": 2, "move_number": 5},
            "status": "in_progress",
            "winner": null
        }
        ```
        or
        {
            "event": "game_end",
            "game_id": 1,
            "board": "XOXOXOOOX",
            "status": "finished",
            "winner": "X"
        }
    """
    await ws_manager.connect(game_id, websocket)
    try:
        while True:
            # The backend only pushes updates: for now, ignore incoming client messages.
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(game_id, websocket)
    except Exception:
        ws_manager.disconnect(game_id, websocket)

@app.get("/ws/docs", tags=["websocket"])
def websocket_docs():
    """
    PUBLIC_INTERFACE
    WebSocket Usage API Documentation for Frontend Integration.

    Returns usage notes, connection URL format, supported events, message structure.
    """
    return JSONResponse({
        "description": "WebSocket endpoint to receive real-time updates for Tic Tac Toe game boards and moves.",
        "endpoint": "/ws/games/{game_id}",
        "connect_example": "ws://<server-host>/ws/games/1",
        "events": [
            {
                "event": "move",
                "payload": {
                    "game_id": 1,
                    "board": "XO---X---",
                    "move": {"position": 4, "symbol": "O", "player_id": 2, "move_number": 5},
                    "status": "in_progress",
                    "winner": None
                }
            },
            {
                "event": "game_end",
                "payload": {
                    "game_id": 1,
                    "board": "XOXOXOOOX",
                    "status": "finished",
                    "winner": "X"
                }
            }
        ],
        "notes": [
            "Connect to `/ws/games/{game_id}`. Each client in the game receives an event on every move or board change.",
            "The server only pushes events. You do not need to send data except a keepalive (if you want to prevent disconnect).",
            "Message payloads are always JSON.",
            "Listen for `event` field to determine update type."
        ]
    })

# Include routers for users and games (REST)
app.include_router(user_router)
app.include_router(game_router)

@app.get("/")
def health_check():
    """PUBLIC_INTERFACE
    Health check endpoint for the Tic Tac Toe backend.
    """
    return {"message": "Healthy"}

# --- Patch for game move REST endpoint to trigger WS updates ---

async def send_realtime_push(game_id: int, board: str, move: dict, status: str, winner: Any):
    """
    Utility function to broadcast board/move updates (called after move is made).
    """
    event = {
        "event": "move" if status != "finished" else "game_end",
        "game_id": game_id,
        "board": board,
        "move": move if status != "finished" else None,
        "status": status,
        "winner": winner
    }
    await ws_manager.broadcast(game_id, event)

# Patch the regular REST move endpoint to call this
def patch_move_endpoint(app: FastAPI):
    """
    Wrap the 'make_move' endpoint to push WS events.
    """
    # Find the move endpoint from included routers
    for route in app.routes:
        if isinstance(route, APIRoute) and hasattr(route, "endpoint"):
            fn = route.endpoint
            if getattr(fn, "__name__", "") == "make_move":
                # Patch it to call broadcast after move is made
                original = fn

                async def move_with_ws(
                    *args, **kwargs
                ):
                    # Call the original endpoint (it's a coroutine)
                    resp = await original(*args, **kwargs)
                    # Only trigger push on success
                    game_id = kwargs.get("game_id")
                    move_body = kwargs.get("move")
                    if isinstance(resp, dict) and game_id and move_body:
                        # Compose move dict as expected by push
                        move_dict = {
                            "position": move_body.position,
                            "symbol": move_body.symbol,
                            "player_id": move_body.player_id,
                            # Use response's move_number if present
                            "move_number": resp.get("move_number")
                        }
                        # If running inside an event loop, do broadcast in background
                        loop = asyncio.get_running_loop()
                        loop.create_task(send_realtime_push(game_id, resp.get("board"), move_dict, resp.get("status"), resp.get("winner")))
                    return resp

                # Patch (replace) in place
                route.endpoint = move_with_ws
                break

# Patch after app startup/event is handled
@app.on_event("startup")
def setup_move_ws_patch():
    patch_move_endpoint(app)

