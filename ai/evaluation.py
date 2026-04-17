import chess

# Simple piece values
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Piece-square tables for basic positional evaluation
# We use standard simplified tables (flipped for black)
PAWN_PST = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_PST = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_PST = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_PST = [
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_PST = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_PST_MIDGAME = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

def get_pst_value(piece_type, square, color):
    """
    Returns the Piece-Square Table value. 
    White squares are 0-63 (A1 to H8). For black, we mirror the square index.
    """
    if color == chess.BLACK:
        square = chess.square_mirror(square)
        
    if piece_type == chess.PAWN:
        return PAWN_PST[square]
    elif piece_type == chess.KNIGHT:
        return KNIGHT_PST[square]
    elif piece_type == chess.BISHOP:
        return BISHOP_PST[square]
    elif piece_type == chess.ROOK:
        return ROOK_PST[square]
    elif piece_type == chess.QUEEN:
        return QUEEN_PST[square]
    elif piece_type == chess.KING:
        return KING_PST_MIDGAME[square]
    return 0

def evaluate_board(board: chess.Board, depth: int = 0) -> int:
    """
    Evaluates the board from White's perspective.
    Positive scores favor White, negative favor Black.
    """
    if board.is_checkmate():
        if board.turn == chess.WHITE:
            return -999999 - depth # Black won (Faster mate is more negative)
        else:
            return 999999 + depth # White won (Faster mate is more positive)
            
    if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition() or board.is_repetition(3):
        return 0

    score = 0
    
    # Material and Positional evaluation
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            val = PIECE_VALUES[piece.piece_type] + get_pst_value(piece.piece_type, square, piece.color)
            if piece.color == chess.WHITE:
                score += val
            else:
                score -= val

    # ── Opening development bonus (active for first 20 moves) ──────────────
    # Reward each side for getting minor pieces OFF their starting squares.
    # This prevents the AI from looping the knight while bishops stay home.
    # Each developed knight or bishop = +20 cp.  Center pawn pushed = +15 cp.
    if board.fullmove_number <= 20:
        WHITE_MINOR_STARTS = {chess.B1, chess.G1, chess.C1, chess.F1}
        BLACK_MINOR_STARTS = {chess.B8, chess.G8, chess.C8, chess.F8}

        for sq, piece in board.piece_map().items():
            if piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                if piece.color == chess.WHITE and sq not in WHITE_MINOR_STARTS:
                    score += 20   # White piece developed → good for White
                elif piece.color == chess.BLACK and sq not in BLACK_MINOR_STARTS:
                    score -= 20   # Black piece developed → good for Black (lower White score)

        # Center pawn bonus: pawns on d4/e4 for White, d5/e5 for Black
        CENTER_WHITE = {chess.D4, chess.E4}
        CENTER_BLACK = {chess.D5, chess.E5}
        for sq in CENTER_WHITE:
            p = board.piece_at(sq)
            if p and p.piece_type == chess.PAWN and p.color == chess.WHITE:
                score += 15
        for sq in CENTER_BLACK:
            p = board.piece_at(sq)
            if p and p.piece_type == chess.PAWN and p.color == chess.BLACK:
                score -= 15
                
    # Endgame heuristic to drive checkmate when massive advantage exists
    white_material = sum(PIECE_VALUES[p.piece_type] for p in board.piece_map().values() if p.color == chess.WHITE and p.piece_type != chess.KING)
    black_material = sum(PIECE_VALUES[p.piece_type] for p in board.piece_map().values() if p.color == chess.BLACK and p.piece_type != chess.KING)
    
    endgame_weight = 0
    if white_material + black_material < 3000:
        endgame_weight = 1.0
    elif white_material + black_material < 5000:
        endgame_weight = 0.5
        
    if endgame_weight > 0:
        wk_square = board.king(chess.WHITE)
        bk_square = board.king(chess.BLACK)
        if wk_square is not None and bk_square is not None:
            wk_col, wk_row = chess.square_file(wk_square), chess.square_rank(wk_square)
            bk_col, bk_row = chess.square_file(bk_square), chess.square_rank(bk_square)
            
            dist = abs(wk_col - bk_col) + abs(wk_row - bk_row)
            center_dist_w = max(3 - wk_col, wk_col - 4) + max(3 - wk_row, wk_row - 4)
            center_dist_b = max(3 - bk_col, bk_col - 4) + max(3 - bk_row, bk_row - 4)
            
            if white_material > black_material + 300:
                score += int((14 - dist) * 10 * endgame_weight)
                score += int(center_dist_b * 10 * endgame_weight)
                # Swarm enemy king
                for p_sq, p in board.piece_map().items():
                    if p.color == chess.WHITE and p.piece_type != chess.KING:
                        p_col, p_row = chess.square_file(p_sq), chess.square_rank(p_sq)
                        p_dist = abs(p_col - bk_col) + abs(p_row - bk_row)
                        score += int((14 - p_dist) * endgame_weight)
            elif black_material > white_material + 300:
                score -= int((14 - dist) * 10 * endgame_weight)
                score -= int(center_dist_w * 10 * endgame_weight)
                # Swarm enemy king
                for p_sq, p in board.piece_map().items():
                    if p.color == chess.BLACK and p.piece_type != chess.KING:
                        p_col, p_row = chess.square_file(p_sq), chess.square_rank(p_sq)
                        p_dist = abs(p_col - wk_col) + abs(p_row - wk_row)
                        score -= int((14 - p_dist) * endgame_weight)
                
    return score