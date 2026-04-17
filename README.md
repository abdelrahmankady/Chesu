# ♟️ Chesu — Chess AI

A web-based chess application featuring **Minimax** and **Alpha-Beta Pruning** search algorithms, a fully interactive browser interface, and a real-time analytics dashboard.

---

## 🎯 Overview

Chesu is a playable chess game where the AI opponent **adaptively selects its own search algorithm** based on the current game phase:

| Game Phase | Algorithm | Depth | Reason |
|---|---|---|---|
| Opening (moves 1–6) | Minimax | 2 | Fast brute-force; standard positions |
| Middle game | Alpha-Beta | 3 | Pruning handles growing complexity |
| Endgame / Check | Alpha-Beta | 4 | Maximum depth for forced-mate accuracy |

Every AI move is fully transparent — the analytics dashboard shows which algorithm was chosen, why, how many nodes were explored, how many branches were pruned, and how long it took.

---

## 🧠 Algorithms

### Minimax (Depth 2)
A complete brute-force tree search. Explores every possible move to a given depth, assuming the opponent always plays optimally. No pruning applied.

### Alpha-Beta Pruning (Depth 3 & 4)
An extension of Minimax that maintains two bounds (`α` and `β`) to prune branches that cannot influence the final decision. Significantly reduces the number of nodes explored without changing the result.

**Optimisations applied:**
- **Move ordering** — captures and checks are evaluated first, maximising pruning efficiency
- **Same-piece penalty** — discourages moving the same piece twice in the opening (tempo heuristic)
- **Opening jitter** — ±25 cp random noise during the first 12 moves for game variety
- **Development bonus** — rewards getting minor pieces off starting squares (+20 cp each)
- **Center pawn bonus** — rewards controlling the center with pawns (+15 cp each)

### Board Evaluation
The static evaluation function scores positions from White's perspective:

| Component | Description |
|---|---|
| **Material** | Standard piece values (P=100, N=320, B=330, R=500, Q=900) |
| **Piece-Square Tables** | Positional bonuses based on where each piece stands |
| **Checkmate** | ±999999 adjusted by depth (prefers faster mates) |
| **Development** | Bonus for minor pieces off starting squares (opening) |
| **Endgame Swarm** | Drives pieces toward enemy king in winning endings |

---

## 🗂️ Project Structure

```
Chesu/
│
├── app.py                  # FastAPI backend — REST API for game state & AI moves
├── requirements.txt        # Pinned Python dependencies
├── README.md               # This file
│
├── ai/
│   ├── __init__.py
│   ├── minimax.py          # Pure Minimax implementation
│   ├── alphabeta.py        # Alpha-Beta Pruning implementation
│   ├── evaluation.py       # Static board evaluation function + PSTs
│   └── difficulty.py       # Adaptive algorithm selector (select_algorithm)
│
└── static/
    ├── index.html          # Single-page application shell
    ├── styles.css          # Glassmorphic dark UI styles
    └── script.js           # Board rendering, move handling, API calls
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
# Navigate to the project folder
cd Chesu

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
/usr/bin/python3 main.py
```

Then open your browser and go to:

```
http://127.0.0.1:8004
```

---

## 🎮 How to Play

1. **Make your move** — click a white piece, then click the destination square (valid squares highlight in blue)
2. **Watch the AI respond** — the AI automatically picks its algorithm based on the game phase and moves within ~1 second
3. **Open the panel** — click **"⚙️ Open Game Controls & Analytics"** to see the AI Analytics Dashboard
4. **Read the stats** — after each AI move the dashboard shows:
   - **AI Strategy** — which algorithm was chosen and why
   - **Last Move** — the move played in standard chess notation
   - **Eval Score** — board evaluation in centipawns (positive = White winning)
   - **Nodes Explored** — total tree nodes evaluated by the search
   - **Branches Pruned** — branches cut by Alpha-Beta (N/A for Minimax)
   - **Time Taken** — wall-clock search time in seconds
5. **Start a new game** — click **New Game** or **Play Again** after checkmate

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/state` | Returns current FEN, legal moves, turn, game-over status |
| `POST` | `/api/move` | Submit a player move in UCI format (e.g. `"e2e4"`) |
| `POST` | `/api/ai-move` | Trigger AI move — algorithm auto-selected by game phase |
| `POST` | `/api/reset` | Reset the board to starting position |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, FastAPI, Uvicorn |
| Chess engine | python-chess 1.11.2 |
| Frontend | Vanilla HTML5, CSS3, JavaScript |
| Styling | Glassmorphic dark theme, CSS Grid, Google Fonts |
| Data validation | Pydantic v2 |

---

## 📄 License

MIT — free to use and modify.
