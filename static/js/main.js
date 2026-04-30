let selectedSquare = null;
let legalDestinations = [];

// Helper to convert indices (0-63) to algebraic notation (a8-h1)
function getSquareName(index) {
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const rank = 8 - Math.floor(index / 8);
    const file = files[index % 8];
    return file + rank;
}



// Fetch the game state from Flask Backend

async function fetchGameState() {
    const response = await fetch('/api/state');
    const state = await response.json();
    
    // Log it to verify
    console.log("Game State Received: ", state);

    // Update the text on the screen
    document.getElementById('status').innerText = `Turn: ${state.turn} | Status: ${state.status}`;

    // Send the board portion of the state to be rendered
    renderBoard(state.board);
}

function renderBoard(fen){
    const boardDiv = document.getElementById('board');
    boardDiv.innerHTML = '';

    // Extract just the layout portion of the FEN string and split it into rows
    const ranks = fen.split(' ')[0].split('/');

    ranks.forEach((rank,rowIndex) => {
        for(let char of rank){
            if(isNaN(char)){
                // If the character is a letter, create a square with that piece
                createSquare(boardDiv, char, rowIndex);
            }
            else{
                // If the character is a number, create that many empty squares
                for (let i = 0; i < parseInt(char); i++) {
                    createSquare(boardDiv, null, rowIndex);
                }
            }
        }
        
    });
}




// Helper function to map FEN characters to image filenames
function getPieceImageSrc(pieceChar) {
    // If the character is uppercase, it is White. If lowercase, it is Black.
    const isWhite = pieceChar === pieceChar.toUpperCase();
    const color = isWhite ? 'w' : 'b';
    
    // The filename uses uppercase for the piece type (e.g., 'K', 'Q', 'N')
    const type = pieceChar.toUpperCase();
    
    return `/static/pieces/${color}${type}.svg`;
}




function createSquare(container, piece, rowIndex) {
    const square = document.createElement('div');
    square.className = 'square';
    
    // Calculate whether the square should be light or dark
    const isBlack = (rowIndex + container.children.length) % 2 !== 0;
    square.classList.add(isBlack ? 'black-sq' : 'white-sq');
    
    // If there is a piece, create an image element and add it to the square
    if (piece) {
        const img = document.createElement('img');
        img.src = getPieceImageSrc(piece);
        img.className = 'piece'; // We will style this class in CSS
        
        // Prevent the default browser behavior of ghost-dragging images
        img.draggable = false; 
        
        square.appendChild(img);
    }


    // Identify the square
    const squareIndex = container.children.length;
    const squareName = getSquareName(squareIndex);
    square.dataset.square = squareName;
    
    // Listen for clicks
    square.addEventListener('click', () => handleSquareClick(squareName));
    
    container.appendChild(square);
}



// Handles Square Clicks
async function handleSquareClick(squareName) {
    if (!selectedSquare) {
        // First Click: Ask Python for legal moves
        const response = await fetch(`/api/legal-moves?square=${squareName}`);
        const moves = await response.json();
        
        if (moves.length > 0) {
            selectedSquare = squareName;
            legalDestinations = moves;
            highlightSquares();
        }
    } else {
    // Second Click: Try to move
    if (legalDestinations.includes(squareName)) {
        const response = await fetch('/api/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ from: selectedSquare, to: squareName })
        });

        if (response.ok) {
    const state = await response.json();
    console.log("Move response:", state);
    document.getElementById('status').innerText = `Turn: ${state.turn} | Status: ${state.status}`;
    renderBoard(state.board);
}
    }

    selectedSquare = null;
    legalDestinations = [];
    removeHighlights();
}
}




function highlightSquares() {
    // Clear any existing highlights first 🧹
    removeHighlights();

    // Highlight the clicked piece
    const selectedElement = document.querySelector(`[data-square="${selectedSquare}"]`);
    if (selectedElement) {
        selectedElement.classList.add('selected');
    }

    // Highlight all valid destinations
    legalDestinations.forEach(sq => {
        const destinationElement = document.querySelector(`[data-square="${sq}"]`);
        if (destinationElement) {
            destinationElement.classList.add('legal-move');
        }
    });
}

function removeHighlights() {
    document.querySelectorAll('.square').forEach(sq => {
        sq.classList.remove('selected', 'legal-move');
    });
}


fetchGameState();