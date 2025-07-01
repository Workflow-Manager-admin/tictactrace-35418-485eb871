from fastapi import FastAPI, Depends, HTTPException, status, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
from enum import Enum

app = FastAPI(
    title="Tic Tac Toe Backend API",
    description="API backend for Tic Tac Toe game: user authentication, games, moves, state, and history.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Users", "description": "Operations related to user registration and authentication."},
        {"name": "Games", "description": "Endpoints for creating, joining, and listing games."},
        {"name": "Moves", "description": "Endpoints for submitting moves and getting game state."},
        {"name": "History", "description": "Endpoints for viewing game history."}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---

class UserCreateRequest(BaseModel):
    username: str = Field(..., description="Desired username")
    password: str = Field(..., description="Password")

class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class AuthToken(BaseModel):
    access_token: str = Field(..., description="JWT access token")

class UserInfo(BaseModel):
    user_id: int = Field(..., description="User's unique identifier")
    username: str = Field(..., description="Username")

class GameCreateRequest(BaseModel):
    opponent_username: Optional[str] = Field(None, description="Username of opponent, or null for open game")

class GameInfo(BaseModel):
    game_id: int = Field(..., description="Unique identifier for the game")
    player_x: str = Field(..., description="Username playing as X")
    player_o: Optional[str] = Field(None, description="Username playing as O, if assigned")
    status: str = Field(..., description="Game status: waiting, in_progress, finished")
    winner: Optional[str] = Field(None, description="Winner if the game is finished, else null")
    board: List[List[Optional[str]]] = Field(..., description="Game board as 3x3 list")

class MoveRequest(BaseModel):
    row: int = Field(..., ge=0, le=2, description="Row index (0-2)")
    col: int = Field(..., ge=0, le=2, description="Column index (0-2)")

class MoveInfo(BaseModel):
    move_number: int = Field(..., description="Move number within the game")
    player: str = Field(..., description="Username who made the move")
    row: int = Field(..., ge=0, le=2)
    col: int = Field(..., ge=0, le=2)
    symbol: str = Field(..., description="'X' or 'O'")
    timestamp: str = Field(..., description="Timestamp of move")

class GameHistoryInfo(BaseModel):
    game_id: int = Field(..., description="Unique identifier for the game")
    opponent: str = Field(..., description="Opponent's username")
    status: str = Field(..., description="Result: win/loss/draw/in_progress")
    played_at: str = Field(..., description="Game started timestamp")
    your_symbol: str = Field(..., description="'X' or 'O'")
    moves: List[MoveInfo] = Field(..., description="Moves in the game")


# --- Dependency placeholder: get current user (stub for authentication) ---
def get_current_user(token: str = Query(..., description="Authentication token")) -> UserInfo:
    """
    Placeholder for authentication, should decode and verify the token.
    """
    # This should be implemented with a real token system.
    # Here we simply mock for demo.
    return UserInfo(user_id=1, username="test_user")


# --- Endpoints for Users ---

# PUBLIC_INTERFACE
@app.post("/auth/register", summary="Register new user", tags=["Users"], response_model=AuthToken,
          description="Creates new user account and returns auth token.")
def register_user(user: UserCreateRequest = Body(...)):
    """
    Registers a new user account and returns an authentication token.

    - **username**: Desired username
    - **password**: Password for new account

    Returns:
        AuthToken object with access_token if successful.
    """
    # TODO: Implement database interaction for creating a user.
    return AuthToken(access_token="fake-jwt-token-for-demo")


# PUBLIC_INTERFACE
@app.post("/auth/login", summary="Login user", tags=["Users"], response_model=AuthToken,
          description="Performs user authentication and returns auth token.")
def login_user(user: UserLoginRequest = Body(...)):
    """
    Authenticates a user.

    - **username**: Username
    - **password**: Password

    Returns:
        AuthToken object with access_token if credentials are valid.
    """
    # TODO: Implement authentication.
    return AuthToken(access_token="fake-jwt-token-for-demo")


# --- Game Management ---

# PUBLIC_INTERFACE
@app.post("/games", summary="Create or join a game", tags=["Games"], response_model=GameInfo,
          description="Create a new game or join an open one. Optionally specify opponent.")
def create_game(request: GameCreateRequest = Body(...), current_user: UserInfo = Depends(get_current_user)):
    """
    Create a new game (with or without a specific opponent).
    If an open game exists, join as the second player.
    """
    # TODO: Implement logic using database interface
    example_board = [[None, None, None], [None, None, None], [None, None, None]]
    return GameInfo(
        game_id=123,
        player_x=current_user.username,
        player_o=None,
        status="waiting",
        winner=None,
        board=example_board
    )

# PUBLIC_INTERFACE
@app.post("/games/{game_id}/join", summary="Join an open game", tags=["Games"], response_model=GameInfo,
          description="Join an open game by game ID.")
def join_game(game_id: int, current_user: UserInfo = Depends(get_current_user)):
    """
    Join an existing open game as the second player.

    Args:
        game_id (int): Game identifier

    Returns:
        GameInfo: Current game state after join
    """
    # TODO: Implement logic to join an open game
    return GameInfo(
        game_id=game_id,
        player_x="player1",
        player_o=current_user.username,
        status="in_progress",
        winner=None,
        board=[[None, None, None], [None, None, None], [None, None, None]]
    )

# PUBLIC_INTERFACE
@app.get("/games", summary="List active games for user", tags=["Games"], response_model=List[GameInfo],
          description="List all current/active games for authorized user.")
def list_games(current_user: UserInfo = Depends(get_current_user)):
    """
    Lists all current games for the authenticated user.
    """
    # TODO: Query from database for user's games
    return []


# --- Moves / Game Board State ---

# PUBLIC_INTERFACE
@app.post("/games/{game_id}/move", summary="Submit tic tac toe move", tags=["Moves"], response_model=GameInfo,
          description="Submit a move to the board for the specified game. Returns new game state.")
def submit_move(game_id: int, move: MoveRequest = Body(...), current_user: UserInfo = Depends(get_current_user)):
    """
    Submit a move to the specified game's board.

    Args:
        game_id (int): The game identifier
        move: Row and column indices

    Returns:
        Updated game state as GameInfo
    """
    # TODO: Validate move, update db, check win/draw, and return new game state
    return GameInfo(
        game_id=game_id,
        player_x="player1",
        player_o="player2",
        status="in_progress",
        winner=None,
        board=[[None, None, None], [None, "X", None], [None, None, None]]
    )


# PUBLIC_INTERFACE
@app.get("/games/{game_id}/state", summary="Get state for a game", tags=["Moves"], response_model=GameInfo,
          description="Retrieve the current board and details of a game by ID.")
def get_game_state(game_id: int, current_user: UserInfo = Depends(get_current_user)):
    """
    Get the current state of a tic tac toe board.
    """
    # TODO: Lookup game by ID from database
    return GameInfo(
        game_id=game_id,
        player_x="player1",
        player_o="player2",
        status="in_progress",
        winner=None,
        board=[[None, None, None], [None, "X", None], [None, None, None]]
    )


# --- Game History ---

# PUBLIC_INTERFACE
@app.get("/history", summary="Get game history of user", tags=["History"], response_model=List[GameHistoryInfo],
          description="Retrieve all completed games for the current user including moves and results.")
def get_game_history(current_user: UserInfo = Depends(get_current_user)):
    """
    Get the game history for the current user, including moves and outcomes.
    """
    # TODO: Query from database for user's completed games
    return []


# --- Health Check ---

# PUBLIC_INTERFACE
@app.get("/", tags=["Users"], summary="Health check", description="Basic health check endpoint")
def health_check():
    """Health check endpoint for service availability."""
    return {"message": "Healthy"}
