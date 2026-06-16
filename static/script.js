const PIECE_UNICODE = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
};

const boardEl         = document.getElementById('board');
const btnForceAI      = document.getElementById('btn-force-ai');
const btnReset        = document.getElementById('btn-reset');
const statusIndicator = document.getElementById('status-indicator');
const gameOverPanel   = document.getElementById('game-over-modal');
const sidebar         = document.getElementById('sidebar');
const btnOpen         = document.getElementById('sidebar-open');
const btnClose        = document.getElementById('sidebar-close');

// ── Sidebar toggle ────────────────────────────────────────────────────────────
btnOpen.addEventListener('click',  () => sidebar.classList.remove('closed'));
btnClose.addEventListener('click', () => sidebar.classList.add('closed'));

// ── Game state ────────────────────────────────────────────────────────────────
let legalMovesMap  = {};
let selectedSquare = null;
let isAiThinking   = false;
let isProcessing   = false;
let currentTurn    = 'white';
let gameOver       = false;

// ── Helpers ───────────────────────────────────────────────────────────────────

// FEN index → square name  (0 = a8, 63 = h1)
function indexToSquare(idx) {
    const col = String.fromCharCode('a'.charCodeAt(0) + (idx % 8));
    const row = 8 - Math.floor(idx / 8);
    return `${col}${row}`;
}

// Chess rule: light square when (file-index + rank) is even
function isLightSquare(sqName) {
    const file = sqName.charCodeAt(0) - 'a'.charCodeAt(0); // 0-7
    const rank = parseInt(sqName[1]);                        // 1-8
    return (file + rank) % 2 === 0;
}

function clearStats() {
    ['stat-move','stat-score','stat-nodes','stat-pruned','stat-time'].forEach(id => {
        document.getElementById(id).innerText = '-';
    });
    document.getElementById('stat-algo').innerText   = 'Waiting…';
    document.getElementById('stat-reason').innerText = '—';
}

// ── State fetch & board render ────────────────────────────────────────────────
async function fetchState() {
    try {
        const res  = await fetch('/api/state');
        const data = await res.json();

        currentTurn = data.turn;
        gameOver    = data.is_game_over;

        legalMovesMap = {};
        for (let mv of data.legal_moves) {
            const start = mv.substring(0, 2);
            const end   = mv.substring(2, 4);
            if (!legalMovesMap[start]) legalMovesMap[start] = [];
            legalMovesMap[start].push(end);
        }

        renderBoardFromFEN(data.fen);

        if (data.is_game_over) {
            showGameOver(data.result);
        } else if (currentTurn === 'white' && !isAiThinking) {
            statusIndicator.className = 'status-indicator';
            statusIndicator.innerText = 'Your Turn (White)';
        }
    } catch (err) {
        console.error('fetchState error:', err);
    }
}

function renderBoardFromFEN(fen) {
    boardEl.innerHTML = '';

    const pieces = [];
    for (let r of fen.split(' ')[0].split('/')) {
        for (let c of r) {
            if (!isNaN(c)) {
                for (let i = 0; i < parseInt(c); i++) pieces.push(null);
            } else {
                pieces.push(c);
            }
        }
    }

    for (let i = 0; i < 64; i++) {
        const sqName = indexToSquare(i);
        const div    = document.createElement('div');

        div.className  = `square ${isLightSquare(sqName) ? 'light' : 'dark'}`;
        div.dataset.sq = sqName;

        if (selectedSquare === sqName) {
            div.classList.add('selected');
        } else if (selectedSquare && legalMovesMap[selectedSquare]?.includes(sqName)) {
            div.classList.add('highlight');
        }

        if (pieces[i]) {
            const span      = document.createElement('span');
            span.className  = 'piece';
            span.innerText  = PIECE_UNICODE[pieces[i]];
            const isWhite   = pieces[i] === pieces[i].toUpperCase();
            span.style.color      = isWhite ? '#ffffff' : '#111111';
            span.style.textShadow = isWhite
                ? '0 2px 5px rgba(0,0,0,0.9)'
                : '0 2px 5px rgba(255,255,255,0.6)';
            div.appendChild(span);
        }

        div.addEventListener('click', () => handleSquareClick(sqName));
        boardEl.appendChild(div);
    }
}

// ── User move ─────────────────────────────────────────────────────────────────
async function handleSquareClick(sqName) {
    if (isAiThinking || isProcessing || currentTurn !== 'white' || gameOver) return;

    if (selectedSquare) {
        if (legalMovesMap[selectedSquare]?.includes(sqName)) {
            const move     = `${selectedSquare}${sqName}`;
            selectedSquare = null;
            await submitMove(move);
            return;
        }
        selectedSquare = legalMovesMap[sqName] ? sqName : null;
    } else {
        if (legalMovesMap[sqName]) selectedSquare = sqName;
    }

    await fetchState();
}

async function submitMove(moveStr) {
    isProcessing = true;
    try {
        const res = await fetch('/api/move', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ move: moveStr })
        });
        if (!res.ok) {
            const err = await res.json();
            console.warn('Move rejected:', err.detail);
        }
    } catch (err) {
        console.error('submitMove error:', err);
    } finally {
        isProcessing = false;
    }

    await fetchState();

    if (currentTurn === 'black' && !gameOver) {
        // 800ms pause so the player can see their move before the AI responds
        setTimeout(() => forceAiMove(), 800);
    }
}

// ── AI move ───────────────────────────────────────────────────────────────────
async function forceAiMove() {
    if (isAiThinking || gameOver) return;

    isAiThinking   = true;
    selectedSquare = null;

    statusIndicator.className = 'status-indicator thinking';
    statusIndicator.innerText = 'AI is thinking…';

    clearStats();

    try {
        // No body needed — the AI chooses its own algorithm on the backend
        const res = await fetch('/api/ai-move', { method: 'POST' });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            console.warn('AI move error:', err.detail || res.status);
        } else {
            const data = await res.json();
            if (data.success) {
                document.getElementById('stat-move').innerText  = data.move || 'None';
                document.getElementById('stat-score').innerText = data.score;
                document.getElementById('stat-algo').innerText  = data.algoId   || '-';
                document.getElementById('stat-reason').innerText = data.algoReason || '-';
                document.getElementById('stat-nodes').innerText =
                    typeof data.nodesExplored === 'number'
                        ? data.nodesExplored.toLocaleString() : data.nodesExplored;
                document.getElementById('stat-pruned').innerText =
                    typeof data.branchesPruned === 'number'
                        ? data.branchesPruned.toLocaleString() : data.branchesPruned;
                document.getElementById('stat-time').innerText =
                    typeof data.timeTaken === 'number'
                        ? data.timeTaken.toFixed(3) + ' sec' : data.timeTaken;
            }
        }
    } catch (err) {
        console.error('forceAiMove error:', err);
    }

    isAiThinking = false;
    await fetchState();
}

// ── Reset ─────────────────────────────────────────────────────────────────────
async function resetGame() {
    try { await fetch('/api/reset', { method: 'POST' }); }
    catch (err) { console.error('resetGame error:', err); }

    gameOverPanel.classList.add('hidden');
    selectedSquare = null;
    isAiThinking   = false;
    isProcessing   = false;
    gameOver       = false;
    clearStats();
    await fetchState();
}

// ── Game over ─────────────────────────────────────────────────────────────────
function showGameOver(result) {
    gameOverPanel.classList.remove('hidden');
    let msg = `Result: ${result}`;
    if      (result === '1-0')     msg = 'White wins!';
    else if (result === '0-1')     msg = 'Black wins!';
    else if (result === '1/2-1/2') msg = 'Draw!';
    document.getElementById('game-over-subtext').innerText = msg;
    statusIndicator.className = 'status-indicator';
    statusIndicator.innerText = 'Game Over';
}

// ── Event listeners ───────────────────────────────────────────────────────────
btnReset.addEventListener('click', resetGame);
document.getElementById('btn-reset-modal').addEventListener('click', resetGame);
btnForceAI.addEventListener('click', () => { if (!gameOver) forceAiMove(); });

// ── Init ──────────────────────────────────────────────────────────────────────
fetchState();
