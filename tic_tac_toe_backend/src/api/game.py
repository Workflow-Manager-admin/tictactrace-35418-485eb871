"""Game router for Tic Tac Toe REST API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from .database import SessionLocal
from . import models, schemas, game_logic

router = APIRouter(
    prefix="/games",
    tags=["games"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# PUBLIC_INTERFACE
@router.post("/", response_model=schemas.GameResponse, status_code=status.HTTP_201_CREATED, summary="Create New Game", description="Creates a new Tic Tac Toe game. The creator will be assigned 'X'.")
def create_game(game: schemas.GameCreate, db: Session = Depends(get_db)):
    """Create new game; the creator always goes first (symbol X)."""
    user = db.query(models.User).filter(models.User.id == game.creator_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User (creator) not found")
    game_model = models.Game(creator_id=game.creator_id, board_state="---------", status="waiting")
    db.add(game_model)
    db.commit()
    db.refresh(game_model)
    return game_model

# PUBLIC_INTERFACE
@router.post("/{game_id}/join", response_model=schemas.GameResponse, summary="Join Existing Game", description="Join a waiting game as an opponent (assigned 'O').")
def join_game(game_id: int, req: schemas.GameJoin, db: Session = Depends(get_db)):
    """Opponent joins game. Both creator & opponent must be unique users."""
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "waiting":
        raise HTTPException(status_code=409, detail="Game already started or finished")
    if game.creator_id == req.opponent_id:
        raise HTTPException(status_code=400, detail="Creator and opponent cannot be the same user")
    opponent = db.query(models.User).filter(models.User.id == req.opponent_id).first()
    if not opponent:
        raise HTTPException(status_code=404, detail="Opponent user not found")
    game.opponent_id = req.opponent_id
    game.status = "in_progress"
    db.commit()
    db.refresh(game)
    return game

# PUBLIC_INTERFACE
@router.get("/{game_id}", response_model=schemas.GameResponse, summary="Get Game State", description="Get info and board state for the given game.")
def get_game(game_id: int, db: Session = Depends(get_db)):
    """Retrieve game state and metadata."""
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

# PUBLIC_INTERFACE
@router.get("/{game_id}/board", summary="Get Board State", description="Get board state as string of 9 characters ('X', 'O', '-') and turn info.")
def get_board(game_id: int, db: Session = Depends(get_db)):
    """Return current board state and whose turn."""
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    moves = db.query(models.Move).filter(models.Move.game_id == game_id).order_by(models.Move.move_number).all()
    # Determine next symbol: 'X' if moves are even, 'O' if odd (X always starts)
    next_symbol = "X" if len(moves) % 2 == 0 else "O"
    return {
        "board": game.board_state,
        "status": game.status,
        "winner": game.winner,
        "next_symbol": next_symbol
    }

# PUBLIC_INTERFACE
@router.post("/{game_id}/move", summary="Submit Move", description="Player submits a move (position 0-8) with their symbol ('X' or 'O'). Returns new board state and move info.")
def make_move(game_id: int, move: schemas.MoveCreate, db: Session = Depends(get_db)):
    """Validate and apply move, update board, detect win/draw, and store move."""
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "in_progress":
        raise HTTPException(status_code=409, detail="Can't make move, game not in progress")
    # Validation: correct user (creator/X or opponent/O is allowed turn)
    moves = db.query(models.Move).filter(models.Move.game_id == game_id).order_by(models.Move.move_number).all()
    move_number = len(moves) + 1
    next_symbol = "X" if len(moves) % 2 == 0 else "O"
    player_field = "creator_id" if next_symbol == "X" else "opponent_id"
    correct_player_id = getattr(game, player_field)
    if correct_player_id != move.player_id:
        raise HTTPException(status_code=401, detail="It's not this player's turn.")
    if move.symbol != next_symbol:
        raise HTTPException(status_code=400, detail=f"Expected symbol '{next_symbol}' for this turn.")

    board = game_logic.TicTacToe(game.board_state)
    if not board.is_valid_move(move.position):
        raise HTTPException(status_code=400, detail="Invalid move position.")
    # Make move
    board.make_move(move.position, move.symbol)
    # Save the move
    db_move = models.Move(
        game_id=game.id,
        player_id=move.player_id,
        position=move.position,
        symbol=move.symbol,
        move_number=move_number
    )
    db.add(db_move)

    # Update game board and check winner/draw
    new_board_state = board.current_state()
    game.board_state = new_board_state
    winner = board.check_winner()
    # game.status: in_progress/finished. game.winner: X, O, Draw, or None
    if winner:
        game.status = "finished"
        game.winner = winner
        # Save game history (if not saved yet)
        moves_query = db.query(models.Move).filter(models.Move.game_id == game.id).order_by(models.Move.move_number).all()
        moves_json = [{"player_id": m.player_id, "symbol": m.symbol, "position": m.position, "move_number": m.move_number} for m in moves_query]
        moves_json.append({
            "player_id": move.player_id,
            "symbol": move.symbol,
            "position": move.position,
            "move_number": move_number
        })
        if not game.history:
            game_history = models.GameHistory(
                game_id=game.id,
                moves_json=moves_json,
                result=winner
            )
            db.add(game_history)
    db.commit()
    db.refresh(game)
    return {
        "board": game.board_state,
        "status": game.status,
        "winner": game.winner,
        "move_number": move_number
    }

# PUBLIC_INTERFACE
@router.get("/{game_id}/result", summary="Game Result", description="Show winner (if finished) or status of game.")
def game_result(game_id: int, db: Session = Depends(get_db)):
    """Returns winner or game status."""
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return {
        "status": game.status,
        "winner": game.winner
    }

# PUBLIC_INTERFACE
@router.get("/{game_id}/history", response_model=schemas.GameHistoryResponse, summary="Game Move History", description="Fetch the full move history for this game.")
def game_history(game_id: int, db: Session = Depends(get_db)):
    """Show all moves and final result for finished games."""
    history = db.query(models.GameHistory).filter(models.GameHistory.game_id == game_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="This game does not yet have a completed history.")
    return history

# PUBLIC_INTERFACE
@router.get("/", summary="List/Search Games", description="Retrieve all games (optionally filter by user ID, status, or opponent ID).")
def list_games(
    creator_id: int = Query(None, description="Filter by creator user ID"),
    opponent_id: int = Query(None, description="Filter by opponent user ID"),
    status: str = Query(None, description="Filter game status"),
    db: Session = Depends(get_db)
):
    """List games or filter by creator, opponent, or status."""
    query = db.query(models.Game)
    if creator_id is not None:
        query = query.filter(models.Game.creator_id == creator_id)
    if opponent_id is not None:
        query = query.filter(models.Game.opponent_id == opponent_id)
    if status is not None:
        query = query.filter(models.Game.status == status)
    results = query.order_by(models.Game.created_at.desc()).all()
    return results
