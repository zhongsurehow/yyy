import logging
import json
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from src.game import Game
from src.phases import (
    time_phase,
    placement_phase,
    movement_phase,
    interpretation_phase,
    resolution_phase,
    upkeep_phase,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='../tianji-fix-data-and', static_folder='../tianji-fix-data-and/static')
app.config['SECRET_KEY'] = 'a_very_secret_key_for_tianji_bian!'
socketio = SocketIO(app)

# --- Game Instance and State Management ---
game_instance = None
phase_order = [
    ("TIME", lambda game: time_phase.execute(game.game_state, game)),
    ("PLACEMENT", lambda game: placement_phase.execute(game.game_state)),
    ("MOVEMENT", lambda game: movement_phase.execute(game)),
    ("INTERPRETATION", lambda game: interpretation_phase.execute(game)),
    ("RESOLUTION", lambda game: resolution_phase.execute(game)),
    ("UPKEEP", lambda game: upkeep_phase.execute(game)),
]
current_phase_index = 0

def load_config() -> dict:
    """Loads the configuration from config.json."""
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"FATAL: Could not load config.json. Error: {e}")
        return None

def create_game_from_config() -> Game:
    """Creates a new game instance based on the config file."""
    config = load_config()
    if not config:
        raise ValueError("Failed to load configuration.")

    sim_config = config.get("simulation", {})
    player_names = sim_config.get("player_names", ["Player 1", "Player 2"])
    assets_path = "tianji-fix-data-and/assets"

    game = Game(player_names=player_names, assets_path_str=assets_path)
    game.setup()
    return game

# --- Routes and SocketIO Handlers ---

@app.route('/')
def index():
    """Serve the main game page."""
    logging.info("Serving game.html")
    return render_template('game.html')

def broadcast_game_state(message=""):
    """Serializes and broadcasts the current game state and a message to all clients."""
    if game_instance:
        state_dict = game_instance.game_state.to_dict()
        state_dict["log_message"] = message
        socketio.emit('game_state_update', state_dict)
        logging.info(f"Broadcasted game state update: {message}")

@socketio.on('connect')
def handle_connect():
    """Handle a new client connection and send the current state."""
    logging.info('Client connected')
    if game_instance:
        broadcast_game_state("Client reconnected.")
    else:
        socketio.emit('game_state_update', {"log_message": "Game server is ready. Click 'Start Game' to begin."})

@socketio.on('start_game')
def handle_start_game():
    """Handles the start game event from a client."""
    global game_instance, current_phase_index
    logging.info("Received 'start_game' event.")

    try:
        game_instance = create_game_from_config()
        current_phase_index = 0
        broadcast_game_state("New game started! Advancing to the first phase...")
        # Automatically trigger the first phase
        handle_next_phase()
    except Exception as e:
        logging.error(f"Error starting game: {e}")
        socketio.emit('error', {'message': f"Failed to start game: {e}"})

@socketio.on('next_phase')
def handle_next_phase():
    """Executes the next phase of the game and broadcasts the new state."""
    global current_phase_index
    if not game_instance:
        logging.warning("Received 'next_phase' but no game is active.")
        return

    # Check for winner before proceeding
    winner = game_instance._check_for_winner(game_instance.game_state.current_turn, 10) # Assuming 10 rounds max
    if winner:
        broadcast_game_state(f"Game over! Winner is {winner.name}.")
        return

    if current_phase_index >= len(phase_order):
        current_phase_index = 0
        game_instance.game_state.current_turn += 1
        logging.info(f"--- Starting Round {game_instance.game_state.current_turn} ---")

    phase_name, phase_logic = phase_order[current_phase_index]

    logging.info(f"Executing phase: {phase_name}")
    try:
        phase_logic(game_instance)
        broadcast_game_state(f"Finished {phase_name} phase.")
        current_phase_index += 1
    except Exception as e:
        logging.error(f"Error during {phase_name} phase: {e}", exc_info=True)
        socketio.emit('error', {'message': f"An error occurred during the {phase_name} phase: {e}"})

@socketio.on('reset_game')
def handle_reset_game():
    """Handles the reset game event from a client."""
    global game_instance, current_phase_index
    logging.info("Received 'reset_game' event. Resetting game state.")
    game_instance = None
    current_phase_index = 0
    socketio.emit('game_state_update', {"log_message": "Game has been reset. Click 'Start Game' to begin."})


if __name__ == '__main__':
    logging.info("Starting Tianji Bian server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, use_reloader=False)