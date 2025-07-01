# PUBLIC_INTERFACE
class TicTacToe:
    """Core tic-tac-toe game logic: board update, move validation, win/draw detection."""

    def __init__(self, board_state: str = "---------"):
        """
        :param board_state: 9-character string using -, X, or O
        """
        self.board = list(board_state)
        if len(self.board) != 9:
            raise ValueError("A valid board state has exactly 9 characters.")

    # PUBLIC_INTERFACE
    def is_valid_move(self, position: int) -> bool:
        """Check if move at position is valid (empty space)."""
        return 0 <= position < 9 and self.board[position] == "-"

    # PUBLIC_INTERFACE
    def make_move(self, position: int, symbol: str) -> bool:
        """
        Attempts to apply the move. Returns True if successful, False otherwise.
        """
        if not self.is_valid_move(position):
            return False
        self.board[position] = symbol
        return True

    # PUBLIC_INTERFACE
    def current_state(self) -> str:
        """Return board state as a string."""
        return "".join(self.board)

    # PUBLIC_INTERFACE
    def check_winner(self) -> str:
        """Returns 'X', 'O', 'Draw', or '' if none."""
        wins = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
            (0, 4, 8), (2, 4, 6)              # diags
        ]
        for i, j, k in wins:
            if self.board[i] == self.board[j] == self.board[k] != "-":
                return self.board[i]
        if "-" not in self.board:
            return "Draw"
        return ""

    # PUBLIC_INTERFACE
    def available_moves(self):
        """Returns list of available move positions (int)."""
        return [i for i, v in enumerate(self.board) if v == "-"]
