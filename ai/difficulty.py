import chess
from enum import Enum
from ai.minimax import MinimaxAI
from ai.alphabeta import AlphaBetaAI

class Algorithm(Enum):
    MINIMAX    = "Minimax"
    ALPHABETA3 = "AlphaBeta-3"
    ALPHABETA4 = "AlphaBeta-4"

def select_algorithm(board: chess.Board):
    """
    Adaptively selects the best algorithm based on current game state.
    Returns (ai_instance, algorithm_id, reason_string)

    Selection logic:
      - Opening  (move ≤ 6, pieces ≥ 28) → Minimax Depth 2
        Fast brute-force sufficient; positions are well-studied.
      - Endgame / Critical (pieces ≤ 14 OR board is in check) → Alpha-Beta Depth 4
        Accuracy is paramount; deeper search finds forced mates.
      - Middle game (everything else) → Alpha-Beta Depth 3
        Pruning cuts the search tree significantly; balanced speed/strength.
    """
    fullmove    = board.fullmove_number
    piece_count = len(board.piece_map())
    in_check    = board.is_check()

    if fullmove <= 6 and piece_count >= 28:
        return (
            MinimaxAI(depth=2),
            Algorithm.MINIMAX.value,
            "Opening phase — Minimax Depth 2"
        )

    if piece_count <= 14 or in_check:
        return (
            AlphaBetaAI(depth=4),
            Algorithm.ALPHABETA4.value,
            "Endgame / Critical — Alpha-Beta Depth 4"
        )

    return (
        AlphaBetaAI(depth=3),
        Algorithm.ALPHABETA3.value,
        "Middle game — Alpha-Beta Depth 3"
    )
