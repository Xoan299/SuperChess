from flask import Flask, jsonify, render_template, request
import chess

app = Flask(__name__)

board = chess.Board()

game_state = {
    "board" : board.fen(),
    "turn" : "white",
    "mode" : "classic",
    "status" : "active",
    "dice_roll" : None,
    "dice_used" : False,
    "hands" : {"white" : [] , "black" : []},
    "deck" : [],
    "effects" : {"white" : {} , "black" : {}},
    "room_id" : None,
    "players" : {"white" : None, "black" : None}

}


# Route to serve the webpage

@app.route('/')
def index():
    return render_template('index.html')


# Route to serve the Game Data

@app.route('/api/state')
def get_state():
    return jsonify(game_state)


@app.route('/api/legal-moves')
def get_legal_moves():
    # 1. Get the square name (e.g., 'e2') from the URL parameters
    square_name = request.args.get('square')
    if not square_name:
        return jsonify([])

    # 2. Convert the algebraic name to a python-chess square index
    try:
        from_square = chess.SQUARE_NAMES.index(square_name)
    except ValueError:
        return jsonify([])

    # 3. Check if there is a piece there and if it belongs to the current player
    piece = board.piece_at(from_square)
    current_turn_color = chess.WHITE if game_state["turn"] == "white" else chess.BLACK
    
    if not piece or piece.color != current_turn_color:
        return jsonify([])

    # 4. Filter legal moves for just this specific piece and get destination names
    moves = [chess.SQUARE_NAMES[m.to_square] for m in board.legal_moves if m.from_square == from_square]
    
    return jsonify(moves)


@app.route('/api/move', methods=['POST'])
def make_move():
    data = request.json
    move_uci = f"{data.get('from')}{data.get('to')}"
    
    # Create the move object
    try:
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        return jsonify({"error": "Invalid move format"}), 400

    # Auto-promote pawns to Queen
    piece = board.piece_at(move.from_square)
    if piece and piece.piece_type == chess.PAWN:
        if  (board.turn == chess.WHITE and chess.square_rank(move.to_square) == 7) or \
            (board.turn == chess.BLACK and chess.square_rank(move.to_square) == 0):
            move = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)  # ✅
    if move in board.legal_moves:
        board.push(move)
        
        # Update the game_state dictionary
        game_state["board"] = board.fen()
        game_state["turn"] = "white" if board.turn == chess.WHITE else "black"
        
        # Check game status
        if board.is_checkmate():
            winner = "black" if board.turn == chess.WHITE else "white"
            game_state["status"] = f"checkmate - {winner} wins"
        elif board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            game_state["status"] = "draw"
        elif board.is_check():
            game_state["status"] = "check"
        else:
            game_state["status"] = "active"
            
        return jsonify(game_state)
    
    return jsonify({"error": "Illegal move"}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5001)