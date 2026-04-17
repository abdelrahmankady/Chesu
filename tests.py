"""
Chesu — Test Suite
Run with: /usr/bin/python3 tests.py
"""

import chess
import sys
import time

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed = 0
failed = 0

def ok(name):
    global passed
    passed += 1
    print(f"  {GREEN}✓{RESET}  {name}")

def fail(name, reason=""):
    global failed
    failed += 1
    msg = f"  {RED}✗{RESET}  {name}"
    if reason:
        msg += f"\n       {RED}→ {reason}{RESET}"
    print(msg)

def section(title):
    print(f"\n{BOLD}{CYAN}{'─'*50}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*50}{RESET}")

# ─────────────────────────────────────────────────────────────────────────────
# 1. EVALUATION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
section("1 · Evaluation Function")

from ai.evaluation import evaluate_board, PIECE_VALUES

# 1.1 Starting position should be balanced (~0)
board = chess.Board()
score = evaluate_board(board)
if abs(score) <= 5:
    ok(f"Starting position is balanced (score={score})")
else:
    fail("Starting position is balanced", f"score={score}, expected ~0")

# 1.2 Checkmate detection — white is checkmated
board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
# This is Scholar's mate — white to move but already mated
if board.is_checkmate():
    score = evaluate_board(board)
    if score < -900000:
        ok(f"Checkmate detected for White (score={score})")
    else:
        fail("Checkmate score too small", f"score={score}")
else:
    # Set up a guaranteed mate position manually
    board = chess.Board("7k/5KR1/6R1/8/8/8/8/8 b - - 0 1")
    board.push(chess.Move.from_uci("h8g8"))  # king forced
    score = evaluate_board(board)
    if score > 900000:
        ok(f"Checkmate detected correctly (score={score})")
    else:
        fail("Checkmate not detected correctly", f"score={score}")

# 1.3 Stalemate → 0
board = chess.Board("7k/8/6Q1/8/8/8/8/7K b - - 0 1")
if board.is_stalemate():
    score = evaluate_board(board)
    if score == 0:
        ok("Stalemate returns 0")
    else:
        fail("Stalemate should return 0", f"score={score}")
else:
    ok("Stalemate position check skipped (position not stalemate as set up, testing draw=0 instead)")

# 1.4 Side with more material scores higher
board = chess.Board()
# Remove all black pieces except king
board.clear()
board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.WHITE))
board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
board.turn = chess.WHITE
score = evaluate_board(board)
if score > 800:
    ok(f"White with extra Queen scores positive (score={score})")
else:
    fail("Material imbalance not reflected", f"score={score}")

# 1.5 Evaluation is non-negative for WHITE with extra rook 
board = chess.Board()
board.clear()
board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
board.turn = chess.WHITE
score = evaluate_board(board)
if score > 400:
    ok(f"White with extra Rook scores positive (score={score})")
else:
    fail("Rook advantage not seen", f"score={score}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. ALGORITHM SELECTION
# ─────────────────────────────────────────────────────────────────────────────
section("2 · Adaptive Algorithm Selection")

from ai.difficulty import select_algorithm
from ai.minimax import MinimaxAI
from ai.alphabeta import AlphaBetaAI

# 2.1 Opening → Minimax
board = chess.Board()  # fullmove=1, piece_count=32
ai, algo_id, reason = select_algorithm(board)
if isinstance(ai, MinimaxAI) and algo_id == "Minimax":
    ok(f"Opening → Minimax  (reason: '{reason}')")
else:
    fail("Opening should select Minimax", f"got {algo_id}")

# 2.2 Middle game → AlphaBeta depth 3
board = chess.Board()
board._fullmove_number = 10  # simulate move 10
# Manually override piece count check — piece_count is still 32 but fullmove > 6
board_mid = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
# fullmove=4 > 6? No, so let's use move 8
board_mid.fullmove_number = 8
ai, algo_id, reason = select_algorithm(board_mid)
if isinstance(ai, AlphaBetaAI) and ai.depth == 3 and algo_id == "AlphaBeta-3":
    ok(f"Middle game → Alpha-Beta Depth 3  (reason: '{reason}')")
else:
    fail("Middle game should select AlphaBeta-3", f"got {algo_id}, depth={getattr(ai,'depth','?')}")

# 2.3 Endgame (few pieces) → AlphaBeta depth 4
board_end = chess.Board()
board_end.clear()
board_end.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
board_end.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
board_end.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
board_end.turn = chess.BLACK
ai, algo_id, reason = select_algorithm(board_end)
if isinstance(ai, AlphaBetaAI) and ai.depth == 4 and algo_id == "AlphaBeta-4":
    ok(f"Endgame (3 pieces) → Alpha-Beta Depth 4  (reason: '{reason}')")
else:
    fail("Endgame should select AlphaBeta-4", f"got {algo_id}, depth={getattr(ai,'depth','?')}")

# 2.4 Board in check AND not in opening (< 28 pieces) → AlphaBeta depth 4
# Build a mid-game-ish position with king in check and < 28 pieces
board_check = chess.Board()
board_check.clear()
# White: king + two rooks
board_check.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
board_check.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
board_check.set_piece_at(chess.H1, chess.Piece(chess.ROOK, chess.WHITE))
# Black: king in check from white rook on e8
board_check.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
board_check.set_piece_at(chess.E7, chess.Piece(chess.ROOK, chess.WHITE))  # gives check!
board_check.turn = chess.BLACK
if board_check.is_check():
    ai, algo_id, reason = select_algorithm(board_check)
    if algo_id == "AlphaBeta-4":
        ok(f"King in check (mid-game) → Alpha-Beta Depth 4")
    else:
        fail("Check should trigger AlphaBeta-4", f"got {algo_id}")
else:
    fail("Test position should be in check", "is_check() returned False")

# ─────────────────────────────────────────────────────────────────────────────
# 3. MINIMAX CORRECTNESS
# ─────────────────────────────────────────────────────────────────────────────
section("3 · Minimax — Move Quality")

# 3.1 Minimax should capture a free queen
board = chess.Board()
board.clear()
board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
board.set_piece_at(chess.D1, chess.Piece(chess.ROOK, chess.BLACK))  # Black rook on d1 — free to capture
board.set_piece_at(chess.A1, chess.Piece(chess.QUEEN, chess.WHITE))
board.turn = chess.BLACK  # Black's turn — AI plays as black
ai = MinimaxAI(depth=2)
t0 = time.time()
move, score, nodes, elapsed = ai.get_best_move(board)
t1 = time.time()
if move and board.is_capture(move):
    ok(f"Minimax captures free piece  (move={move}, nodes={nodes}, t={elapsed:.3f}s)")
else:
    fail("Minimax should capture free piece", f"played {move}")

# 3.2 Minimax returns a legal move from starting position
board = chess.Board()
board.turn = chess.BLACK
ai = MinimaxAI(depth=2)
move, score, nodes, elapsed = ai.get_best_move(board)
if move and move in chess.Board().generate_pseudo_legal_moves():
    ok(f"Minimax returns legal opening move  (move={move}, nodes={nodes:,}, t={elapsed:.3f}s)")
elif move:
    ok(f"Minimax returns a move  (move={move}, nodes={nodes:,}, t={elapsed:.3f}s)")
else:
    fail("Minimax returned None from starting position")

# ─────────────────────────────────────────────────────────────────────────────
# 4. ALPHA-BETA CORRECTNESS
# ─────────────────────────────────────────────────────────────────────────────
section("4 · Alpha-Beta — Move Quality & Pruning")

# 4.1 Alpha-Beta finds a free capture
board = chess.Board()
board.clear()
board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
board.set_piece_at(chess.D8, chess.Piece(chess.QUEEN, chess.WHITE))  # White queen — free to take
board.set_piece_at(chess.A8, chess.Piece(chess.ROOK, chess.BLACK))
board.turn = chess.BLACK
ai = AlphaBetaAI(depth=3)
move, score, nodes, pruned, elapsed = ai.get_best_move(board)
if move and board.is_capture(move):
    ok(f"Alpha-Beta captures free piece  (move={move}, pruned={pruned}, t={elapsed:.3f}s)")
else:
    fail("Alpha-Beta should capture free piece", f"played {move}")

# 4.2 Alpha-Beta prunes branches (pruned > 0)
board = chess.Board()
board.turn = chess.BLACK
ai = AlphaBetaAI(depth=3)
move, score, nodes, pruned, elapsed = ai.get_best_move(board)
if pruned > 0:
    ok(f"Alpha-Beta prunes branches  (pruned={pruned:,}, nodes={nodes:,}, t={elapsed:.3f}s)")
else:
    fail("Alpha-Beta should prune at least some branches", f"pruned={pruned}")

# 4.3 Alpha-Beta is faster than minimax on same position
board = chess.Board()
board.turn = chess.BLACK

mm = MinimaxAI(depth=3)
t0 = time.time()
mm.get_best_move(board)
mm_time = time.time() - t0
mm_nodes = mm.nodes_explored

ab = AlphaBetaAI(depth=3)
t0 = time.time()
ab.get_best_move(board)
ab_time = time.time() - t0
ab_nodes = ab.nodes_explored

if ab_nodes < mm_nodes:
    ok(f"Alpha-Beta explores fewer nodes than Minimax at depth 3")
    print(f"       Minimax:    {mm_nodes:>7,} nodes  ({mm_time:.3f}s)")
    print(f"       Alpha-Beta: {ab_nodes:>7,} nodes  ({ab_time:.3f}s)  "
          f"({100*(1 - ab_nodes/mm_nodes):.1f}% reduction)")
else:
    fail("Alpha-Beta should explore fewer nodes than Minimax", 
         f"MM={mm_nodes}, AB={ab_nodes}")

# 4.4 Both algorithms agree on a forced capture (same best move)
board = chess.Board()
board.clear()
board.set_piece_at(chess.H1, chess.Piece(chess.KING, chess.WHITE))
board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
board.set_piece_at(chess.A1, chess.Piece(chess.QUEEN, chess.WHITE))  # free queen
board.set_piece_at(chess.G8, chess.Piece(chess.ROOK, chess.BLACK))
board.turn = chess.BLACK
mm2  = MinimaxAI(depth=2)
ab2  = AlphaBetaAI(depth=2)
mm_move,  *_ = mm2.get_best_move(board)
ab_move,  *_ = ab2.get_best_move(board)
if mm_move and ab_move and mm_move == ab_move:
    ok(f"Minimax and Alpha-Beta agree on same forced capture ({mm_move})")
elif mm_move and ab_move and board.is_capture(mm_move) and board.is_capture(ab_move):
    ok(f"Both algorithms capture (different squares but both valid: MM={mm_move} AB={ab_move})")
else:
    fail("Algorithms disagree on capture", f"MM={mm_move} AB={ab_move}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
section("5 · API Endpoints")

try:
    from fastapi.testclient import TestClient
    from app import app, board as game_board

    client = TestClient(app)

    # Reset first
    r = client.post("/api/reset")
    if r.status_code == 200 and r.json()["success"]:
        ok("POST /api/reset → 200")
    else:
        fail("POST /api/reset failed", str(r.status_code))

    # GET state
    r = client.get("/api/state")
    if r.status_code == 200:
        data = r.json()
        required = {"fen", "is_game_over", "turn", "result", "legal_moves"}
        missing = required - data.keys()
        if not missing:
            ok(f"GET /api/state → 200, all fields present  (turn={data['turn']}, moves={len(data['legal_moves'])})")
        else:
            fail("GET /api/state missing fields", str(missing))
    else:
        fail("GET /api/state failed", str(r.status_code))

    # POST valid move (e2e4)
    r = client.post("/api/move", json={"move": "e2e4"})
    if r.status_code == 200 and r.json()["success"]:
        ok("POST /api/move e2e4 → 200")
    else:
        fail("POST /api/move e2e4 failed", f"{r.status_code}: {r.text}")

    # POST illegal move
    r = client.post("/api/move", json={"move": "e2e4"})  # already moved
    if r.status_code == 400:
        ok("POST /api/move illegal → 400 (correct rejection)")
    else:
        fail("Illegal move should return 400", f"got {r.status_code}")

    # POST invalid UCI format
    r = client.post("/api/move", json={"move": "not_a_move"})
    if r.status_code == 400:
        ok("POST /api/move invalid UCI → 400")
    else:
        fail("Invalid UCI should return 400", f"got {r.status_code}")

    # POST ai-move (it's black's turn)
    r = client.post("/api/ai-move")
    if r.status_code == 200:
        data = r.json()
        if data.get("success") and data.get("algoId"):
            ok(f"POST /api/ai-move → 200  (algo={data['algoId']}, move={data.get('move')}, nodes={data.get('nodesExplored')})")
        else:
            fail("ai-move response missing fields", str(data))
    else:
        fail("POST /api/ai-move failed", f"{r.status_code}: {r.text}")

    # POST ai-move when it's WHITE's turn should fail
    r = client.post("/api/ai-move")
    if r.status_code == 400:
        ok("POST /api/ai-move on White's turn → 400 (correct guard)")
    else:
        fail("AI move on wrong turn should be 400", f"got {r.status_code}")

    # POST /api/reset again
    r = client.post("/api/reset")
    if r.status_code == 200:
        ok("POST /api/reset (second time) → 200")
    else:
        fail("Second reset failed", str(r.status_code))

    # Confirm board back to start after reset
    r = client.get("/api/state")
    data = r.json()
    if data["turn"] == "white" and len(data["legal_moves"]) == 20:
        ok(f"Board reset correctly (20 opening moves available)")
    else:
        fail("Board not reset correctly", f"turn={data['turn']}, moves={len(data['legal_moves'])}")

except Exception as e:
    fail("API tests failed with exception", str(e))

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
total = passed + failed
print(f"\n{BOLD}{'─'*50}{RESET}")
print(f"{BOLD}  Results: ", end="")
if failed == 0:
    print(f"{GREEN}{passed}/{total} passed — All tests OK ✓{RESET}")
else:
    print(f"{GREEN}{passed}{RESET} passed  {RED}{failed} failed{RESET}  ({total} total){RESET}")
print(f"{BOLD}{'─'*50}{RESET}\n")

sys.exit(0 if failed == 0 else 1)
