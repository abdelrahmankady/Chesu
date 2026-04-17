import chess
import time
from typing import Tuple, Optional
from ai.evaluation import evaluate_board

class AlphaBetaAI:
    def __init__(self, depth: int):
        self.depth = depth
        self.nodes_explored = 0
        self.branches_pruned = 0
        
    def get_best_move(self, board: chess.Board) -> Tuple[Optional[chess.Move], int, int, int, float]:
        """
        Returns (best_move, evaluation_score, nodes_explored, branches_pruned, time_taken)
        """
        self.nodes_explored = 0
        self.branches_pruned = 0
        start_time = time.time()
        
        best_move, score = self._alphabeta_root(board, self.depth, -float('inf'), float('inf'), board.turn == chess.WHITE)
        
        end_time = time.time()
        time_taken = end_time - start_time
        
        return best_move, score, self.nodes_explored, self.branches_pruned, time_taken
        
    def _alphabeta_root(self, board: chess.Board, depth: int, alpha: float, beta: float, is_maximizing: bool) -> Tuple[Optional[chess.Move], int]:
        import random
        best_moves = []
        
        if is_maximizing:
            best_score = -float('inf')
        else:
            best_score = float('inf')
        
        # Opening heuristics (active during the first 12 full moves)
        in_opening = board.fullmove_number <= 12
        JITTER = 25  # ±25 cp — enough to vary equal moves without overriding tactics

        # Detect the last move this side made (2 plies back in the move stack).
        # Used to penalise moving the same piece twice in a row (wastes tempo).
        prev_own_move = None
        if in_opening and len(board.move_stack) >= 2:
            prev_own_move = board.move_stack[-2]  # -1 = opponent's last, -2 = our last
            
        legal_moves = list(board.legal_moves)
        legal_moves.sort(key=lambda m: (board.is_capture(m), board.gives_check(m)), reverse=True)
        if not legal_moves:
            return None, evaluate_board(board, depth)
            
        for move in legal_moves:
            board.push(move)
            score = self._alphabeta(board, depth - 1, alpha, beta, not is_maximizing)
            board.pop()
            
            if in_opening:
                # Random jitter for opening variety
                score += random.randint(-JITTER, JITTER)

                # Penalise moving the same piece twice unless it's a capture.
                # +35 raises the score from White's view → looks worse for Black
                # (Black minimises, so it will prefer moves WITHOUT this penalty).
                if (prev_own_move is not None
                        and move.from_square == prev_own_move.to_square
                        and not board.is_capture(move)):
                    if is_maximizing:
                        score -= 35   # Worse for White
                    else:
                        score += 35   # Worse for Black
            
            if is_maximizing:
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
                beta = min(beta, best_score)
                
            if beta <= alpha:
                self.branches_pruned += 1
                break
                
        
        best_move = random.choice(best_moves) if best_moves else None
        return best_move, int(best_score)
        
    def _alphabeta(self, board: chess.Board, depth: int, alpha: float, beta: float, is_maximizing: bool) -> int:
        self.nodes_explored += 1
        
        if depth == 0 or board.is_game_over():
            return evaluate_board(board, depth)
            
        if is_maximizing:
            best_score = -float('inf')
            legal_moves = list(board.legal_moves)
            legal_moves.sort(key=lambda m: (board.is_capture(m), board.gives_check(m)), reverse=True)
            for move in legal_moves:
                board.push(move)
                score = self._alphabeta(board, depth - 1, alpha, beta, False)
                board.pop()
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                
                if beta <= alpha:
                    self.branches_pruned += 1
                    break  # Beta cut-off
            return best_score
        else:
            best_score = float('inf')
            legal_moves = list(board.legal_moves)
            legal_moves.sort(key=lambda m: (board.is_capture(m), board.gives_check(m)), reverse=True)
            for move in legal_moves:
                board.push(move)
                score = self._alphabeta(board, depth - 1, alpha, beta, True)
                board.pop()
                best_score = min(best_score, score)
                beta = min(beta, best_score)
                
                if beta <= alpha:
                    self.branches_pruned += 1
                    break  # Alpha cut-off
            return best_score
