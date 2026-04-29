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

if __name__ == '__main__':
    app.run(debug = True)






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




