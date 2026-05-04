from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import chess
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'  # Required for session

# Store multiple games (keyed by game_id)
games = {}

# Available game modes
GAME_MODES = {
    "classic": {
        "name": "Classic Chess",
        "description": "Standard chess rules",
        "uses_dice": False,
        "uses_cards": False
    },
    "dice": {
        "name": "Dice Chess",
        "description": "Roll dice to determine which pieces can move",
        "uses_dice": True,
        "uses_cards": False
    },
    "cards": {
        "name": "Card Chess",
        "description": "Draw cards for special abilities",
        "uses_dice": False,
        "uses_cards": True
    },
    "super": {
        "name": "SuperChess",
        "description": "Dice + Cards combined for maximum chaos",
        "uses_dice": True,
        "uses_cards": True
    }
}


def create_game(mode="classic"):
    """Create a new game with the specified mode."""
    game_id = str(uuid.uuid4())[:8]
    board = chess.Board()

    games[game_id] = {
        "board_obj": board,
        "board": board.fen(),
        "turn": "white",
        "mode": mode,
        "status": "active",
        "dice_roll": None,
        "dice_used": False,
        "hands": {"white": [], "black": []},
        "deck": [],
        "effects": {"white": {}, "black": {}},
        "players": {"white": None, "black": None}
    }

    return game_id


# --- Routes ---

@app.route('/')
def lobby():
    """Serve the lobby page."""
    return render_template('lobby.html', game_modes=GAME_MODES)


@app.route('/create-game', methods=['POST'])
def create_game_route():
    """Create a new game and redirect to it."""
    mode = request.form.get('mode', 'classic')

    if mode not in GAME_MODES:
        mode = 'classic'

    game_id = create_game(mode)
    return redirect(url_for('game', game_id=game_id))


@app.route('/game/<game_id>')
def game(game_id):
    """Serve the game board for a specific game."""
    if game_id not in games:
        return redirect(url_for('lobby'))

    return render_template('index.html', game_id=game_id)


@app.route('/api/modes')
def get_modes():
    """Return available game modes."""
    return jsonify(GAME_MODES)


@app.route('/api/state/<game_id>')
def get_state(game_id):
    """Get state for a specific game."""
    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    game = games[game_id]
    # Return state without the board object
    return jsonify({
        "board": game["board"],
        "turn": game["turn"],
        "mode": game["mode"],
        "status": game["status"],
        "dice_roll": game["dice_roll"],
        "dice_used": game["dice_used"],
        "hands": game["hands"],
        "effects": game["effects"],
        "mode_info": GAME_MODES[game["mode"]]
    })


@app.route('/api/legal-moves/<game_id>')
def get_legal_moves(game_id):
    """Get legal moves for a specific game."""
    if game_id not in games:
        return jsonify([])

    game = games[game_id]
    board = game["board_obj"]

    square_name = request.args.get('square')
    if not square_name:
        return jsonify([])

    try:
        from_square = chess.SQUARE_NAMES.index(square_name)
    except ValueError:
        return jsonify([])

    piece = board.piece_at(from_square)
    current_turn_color = chess.WHITE if game["turn"] == "white" else chess.BLACK

    if not piece or piece.color != current_turn_color:
        return jsonify([])

    moves = [chess.SQUARE_NAMES[m.to_square] for m in board.legal_moves if m.from_square == from_square]

    return jsonify(moves)


@app.route('/api/move/<game_id>', methods=['POST'])
def make_move(game_id):
    """Make a move in a specific game."""
    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    game = games[game_id]
    board = game["board_obj"]

    data = request.json
    move_uci = f"{data.get('from')}{data.get('to')}"

    try:
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        return jsonify({"error": "Invalid move format"}), 400

    # Auto-promote pawns to Queen
    piece = board.piece_at(move.from_square)
    if piece and piece.piece_type == chess.PAWN:
        if (board.turn == chess.WHITE and chess.square_rank(move.to_square) == 7) or \
                (board.turn == chess.BLACK and chess.square_rank(move.to_square) == 0):
            move = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)

    if move in board.legal_moves:
        board.push(move)

        game["board"] = board.fen()
        game["turn"] = "white" if board.turn == chess.WHITE else "black"

        if board.is_checkmate():
            winner = "black" if board.turn == chess.WHITE else "white"
            game["status"] = f"checkmate - {winner} wins"
        elif board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            game["status"] = "draw"
        elif board.is_check():
            game["status"] = "check"
        else:
            game["status"] = "active"

        return jsonify({
            "board": game["board"],
            "turn": game["turn"],
            "mode": game["mode"],
            "status": game["status"],
            "mode_info": GAME_MODES[game["mode"]]
        })

    return jsonify({"error": "Illegal move"}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5001)
