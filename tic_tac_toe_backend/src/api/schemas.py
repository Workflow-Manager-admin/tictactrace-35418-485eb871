from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# -- User schemas --

# PUBLIC_INTERFACE
class UserBase(BaseModel):
    """Base schema for User."""
    username: str = Field(..., description="Username of the user")

# PUBLIC_INTERFACE
class UserCreate(UserBase):
    """Schema for creating a user."""
    pass

# PUBLIC_INTERFACE
class UserResponse(UserBase):
    """Schema for returning user data."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# -- Game schemas --

# PUBLIC_INTERFACE
class GameBase(BaseModel):
    """Base schema for Game."""
    creator_id: int

# PUBLIC_INTERFACE
class GameCreate(GameBase):
    """Schema for creating a game."""
    pass

# PUBLIC_INTERFACE
class GameJoin(BaseModel):
    """Schema for joining game."""
    opponent_id: int

# PUBLIC_INTERFACE
class GameResponse(GameBase):
    """Schema for returning game info."""
    id: int
    board_state: str
    status: str
    winner: Optional[str]
    created_at: datetime
    opponent_id: Optional[int]

    class Config:
        orm_mode = True

# -- Move schemas --

# PUBLIC_INTERFACE
class MoveBase(BaseModel):
    """Base schema for Move."""
    player_id: int
    position: int
    symbol: str

# PUBLIC_INTERFACE
class MoveCreate(MoveBase):
    """Schema for submitting a move."""
    pass

# PUBLIC_INTERFACE
class MoveResponse(MoveBase):
    """Schema for returning move info."""
    id: int
    game_id: int
    move_number: int
    timestamp: datetime

    class Config:
        orm_mode = True

# -- GameHistory schemas --

# PUBLIC_INTERFACE
class GameHistoryResponse(BaseModel):
    """Schema for returning game history."""
    id: int
    game_id: int
    moves_json: List[dict]
    result: str
    finished_at: datetime

    class Config:
        orm_mode = True
