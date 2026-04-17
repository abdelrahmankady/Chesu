import chess
import time
from typing import Tuple, Optional
from ai.evaluation import evaluate_board

class MinimaxAI:
    def __init__(self, depth: int):
        self.depth = depth
        self.nodes_explored = 0
        
    def get_best_move(self, board: chess.Board) -> Tuple[Optional[chess.Move], int, int, float]:
        """
        Returns (best_move, evaluation_score, nodes_explored, time_taken)
        """
        self.nodes_explored = 0
        start_time = time.time()
        
        best_move, score = self._minimax_root(board, self.depth, board.turn == chess.WHITE)
        
        end_time = time.time()
        time_taken = end_time - start_time
        
        return best_move, score, self.nodes_explored, time_taken
        
    def _minimax_root(self, board: chess.Board, depth: int, is_maximizing: bool) -> Tuple[Optional[chess.Move], int]:
        import random
        best_moves = []
        
        if is_maximizing:
            best_score = -float('inf')
        else:
            best_score = float('inf')
        
        # Opening heuristics (active during the first 12 full moves)
        in_opening = board.fullmove_number <= 12
        JITTER = 25

        # Penalise moving the same piece twice in a row during the opening
        prev_own_move = None
        if in_opening and len(board.move_stack) >= 2:
            prev_own_move = board.move_stack[-2]
            
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None, evaluate_board(board, depth)
            
        for move in legal_moves:
            board.push(move)
            score = self._minimax(board, depth - 1, not is_maximizing)
            board.pop()
            
            if in_opening:
                score += random.randint(-JITTER, JITTER)

                if (prev_own_move is not None
                        and move.from_square == prev_own_move.to_square
                        and not board.is_capture(move)):
                    if is_maximizing:
                        score -= 35
                    else:
                        score += 35
            
            if is_maximizing:
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
            else:
                if score < best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
                    
        best_move = random.choice(best_moves) if best_moves else None
        return best_move, int(best_score)
        
    def _minimax(self, board: chess.Board, depth: int, is_maximizing: bool) -> int:
        self.nodes_explored += 1
        
        if depth == 0 or board.is_game_over():
            return evaluate_board(board, depth)
            
        if is_maximizing:
            best_score = -float('inf')
            for move in board.legal_moves:
                board.push(move)
                score = self._minimax(board, depth - 1, False)
                board.pop()
                best_score = max(best_score, score)
            return best_score
        else:
            best_score = float('inf')
            for move in board.legal_moves:
                board.push(move)
                score = self._minimax(board, depth - 1, True)
                board.pop()
                best_score = min(best_score, score)
            return best_score
