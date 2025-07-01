from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# PUBLIC_INTERFACE
class User(Base):
    """User of Tic Tac Toe game."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    games = relationship("Game", back_populates="creator", foreign_keys="Game.creator_id")
    moves = relationship("Move", back_populates="player")

# PUBLIC_INTERFACE
class Game(Base):
    """Represents a tic tac toe game session."""
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    opponent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    board_state = Column(String, default="---------", nullable=False)  # 9 chars: -, X, or O
    status = Column(String, default="waiting")  # waiting, in_progress, finished
    winner = Column(String, nullable=True)      # "X", "O", "Draw", or None
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="games", foreign_keys=[creator_id])
    moves = relationship("Move", back_populates="game")
    history = relationship("GameHistory", back_populates="game", uselist=False)

# PUBLIC_INTERFACE
class Move(Base):
    """Represents a single move in a tic tac toe game."""
    __tablename__ = "moves"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    position = Column(Integer, nullable=False)  # 0~8 for 3x3 board
    symbol = Column(String, nullable=False)     # "X" or "O"
    move_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="moves")
    player = relationship("User", back_populates="moves")

# PUBLIC_INTERFACE
class GameHistory(Base):
    """Stores the history of a finished game."""
    __tablename__ = "game_histories"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), unique=True)
    moves_json = Column(JSON, nullable=False)    # List of moves with symbols and positions
    result = Column(String, nullable=False)      # "X", "O", or "Draw"
    finished_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="history")
