from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import chess
import uvicorn
import threading

from ai.difficulty import select_algorithm
from ai.alphabeta import AlphaBetaAI

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global game state — protected by a lock to prevent race conditions
board      = chess.Board()
board_lock = threading.Lock()

class MoveRequest(BaseModel):
    move: str  # UCI format e.g. "e2e4"

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/api/state")
def get_state():
    with board_lock:
        legal_moves_uci = [move.uci() for move in board.legal_moves]
        return {
            "fen":          board.fen(),
            "is_game_over": board.is_game_over(),
            "turn":         "white" if board.turn == chess.WHITE else "black",
            "result":       board.result() if board.is_game_over() else "*",
            "legal_moves":  legal_moves_uci,
            "fullmove":     board.fullmove_number,
            "piece_count":  len(board.piece_map()),
            "in_check":     board.is_check(),
        }

@app.post("/api/move")
def make_move(req: MoveRequest):
    with board_lock:
        try:
            move = chess.Move.from_uci(req.move)
            if move in board.legal_moves:
                board.push(move)
                return {"success": True}

            # Auto-promote pawns to Queen when no promotion specified
            if move.promotion is None:
                move_with_promo = chess.Move(
                    move.from_square, move.to_square, promotion=chess.QUEEN
                )
                if move_with_promo in board.legal_moves:
                    board.push(move_with_promo)
                    return {"success": True}

            raise HTTPException(status_code=400, detail="Illegal move")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid move format")

@app.post("/api/ai-move")
def make_ai_move():
    with board_lock:
        if board.is_game_over():
            raise HTTPException(status_code=400, detail="Game is over")
        if board.turn == chess.WHITE:
            raise HTTPException(status_code=400, detail="It is not the AI's turn")

        # AI selects its own algorithm based on game state
        ai_agent, algo_id, algo_reason = select_algorithm(board)

        val_tuple = ai_agent.get_best_move(board)

        if isinstance(ai_agent, AlphaBetaAI):
            best_move, score, nodes_explored, branches_pruned, time_taken = val_tuple
        else:
            best_move, score, nodes_explored, time_taken = val_tuple
            branches_pruned = "N/A"

        san_move = ""
        if best_move:
            san_move = board.san(best_move)
            board.push(best_move)

        return {
            "success":        True,
            "move":           san_move,
            "score":          score,
            "nodesExplored":  nodes_explored,
            "branchesPruned": branches_pruned,
            "timeTaken":      time_taken,
            "algoId":         algo_id,
            "algoReason":     algo_reason,
        }

@app.post("/api/reset")
def reset_game():
    with board_lock:
        board.reset()
    return {"success": True}

if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Starting Chesu...")
    print("   Open your browser at: http://127.0.0.1:8004\n")
    uvicorn.run("app:app", host="127.0.0.1", port=8004, reload=True)
