let selectedSquare = null;
let legalDestinations = [];

// Use GAME_ID passed from template
const gameId = typeof GAME_ID !== 'undefined' ? GAME_ID : null;

// ================= API HELPERS =================

async function fetchState() {
    if (!gameId) return null;
    const res = await fetch(`/api/state/${gameId}`);
    return res.json();
}

async function fetchLegalMoves(square) {
    if (!gameId) return [];
    const res = await fetch(`/api/legal-moves/${gameId}?square=${square}`);
    return res.json();
}

async function sendMove(from, to) {
    if (!gameId) return null;
    const res = await fetch(`/api/move/${gameId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from, to })
    });
    return res.json();
}

function updateStatus(state) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = `Turn: ${state.turn} | Status: ${state.status}`;

    const modeBadge = document.getElementById('mode-badge');
    if (modeBadge && state.mode_info) {
        modeBadge.textContent = state.mode_info.name;
    }
}

// ================= HELPERS =================

// Convert index (0–63) → a8–h1
function getSquareName(index) {
    const files = ['a','b','c','d','e','f','g','h'];
    const rank = 8 - Math.floor(index / 8);
    const file = files[index % 8];
    return file + rank;
}

// Map FEN → image
function getPieceImageSrc(pieceChar) {
    const isWhite = pieceChar === pieceChar.toUpperCase();
    const color = isWhite ? 'w' : 'b';
    const type = pieceChar.toUpperCase();
    return `/static/pieces/${color}${type}.svg`;
}

// ================= FETCH + RENDER =================

async function fetchGameState() {
    const state = await fetchState();
    if (!state) return;

    console.log("Game State:", state);

    updateStatus(state);
    renderBoard(state.board);
}

function renderBoard(fen) {
    const boardDiv = document.getElementById('board');
    boardDiv.innerHTML = '';

    const ranks = fen.split(' ')[0].split('/');

    ranks.forEach((rank, rowIndex) => {
        for (let char of rank) {
            if (isNaN(char)) {
                createSquare(boardDiv, char, rowIndex);
            } else {
                for (let i = 0; i < parseInt(char); i++) {
                    createSquare(boardDiv, null, rowIndex);
                }
            }
        }
    });
}

// ================= BOARD =================

function createSquare(container, piece, rowIndex) {
    const square = document.createElement('div');
    square.className = 'square';

    const isBlack = (rowIndex + container.children.length) % 2 !== 0;
    square.classList.add(isBlack ? 'black-sq' : 'white-sq');

    if (piece) {
        const img = document.createElement('img');
        img.src = getPieceImageSrc(piece);
        img.className = 'piece';
        img.draggable = false;
        square.appendChild(img);
    }

    const squareIndex = container.children.length;
    const squareName = getSquareName(squareIndex);
    square.dataset.square = squareName;

    square.addEventListener('click', () => handleSquareClick(squareName));

    container.appendChild(square);
}

// ================= CLICK HANDLER =================

async function handleSquareClick(squareName) {
    if (!selectedSquare) {
        const moves = await fetchLegalMoves(squareName);

        if (moves.length > 0) {
            selectedSquare = squareName;
            legalDestinations = moves;
            highlightSquares();
        }
    } else {
        if (legalDestinations.includes(squareName)) {
            const state = await sendMove(selectedSquare, squareName);

            if (state) {
                console.log("Move response:", state);
                updateStatus(state);
                renderBoard(state.board);
            }
        }

        selectedSquare = null;
        legalDestinations = [];
        removeHighlights();
    }
}

// ================= UI =================

function highlightSquares() {
    removeHighlights();

    const selectedEl = document.querySelector(`[data-square="${selectedSquare}"]`);
    if (selectedEl) {
        selectedEl.classList.add('selected');
    }

    legalDestinations.forEach(sq => {
        const el = document.querySelector(`[data-square="${sq}"]`);
        if (el) {
            el.classList.add('legal-move');
        }
    });
}

function removeHighlights() {
    document.querySelectorAll('.square').forEach(sq => {
        sq.classList.remove('selected', 'legal-move');
    });
}

// ================= INIT =================

fetchGameState();