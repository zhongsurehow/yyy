import eventlet
eventlet.monkey_patch()

import logging
import io
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit

from src.game import Game

# --- Logging Setup ---
# A custom handler to capture logs in a list
class ListLogHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_records = []

    def emit(self, record):
        self.log_records.append(self.format(record))

    def clear(self):
        self.log_records = []

# Basic config for the app logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Setup the story logger to be captured by our custom handler
story_logger = logging.getLogger("story_logger")
story_logger.setLevel(logging.INFO)
story_logger.propagate = False # Prevent duplicate logs in the console
list_log_handler = ListLogHandler()
list_log_handler.setFormatter(logging.Formatter('%(message)s'))
story_logger.addHandler(list_log_handler)


# --- Flask & SocketIO Setup ---
app = Flask(__name__, static_folder='tianji-fix-data-and/static', template_folder='tianji-fix-data-and')
app.config['SECRET_KEY'] = 'a_very_secret_key_for_tianji_bian!'
socketio = SocketIO(app, async_mode='eventlet')

# --- Game Instance ---
game = Game(player_names=["玩家一", "玩家二"], assets_path_str="tianji-fix-data-and/assets")
game.setup() # Initialize the game state on startup

# --- Routes ---
@app.route('/')
def index():
    """Serve the main game page."""
    logging.info("Serving game.html")
    return render_template('game.html')

# --- Socket.IO Handlers ---
@socketio.on('connect')
def handle_connect():
    """Handle a new client connection."""
    logging.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle a client disconnection."""
    logging.info('Client disconnected')

# --- Game Logic Handlers ---

@socketio.on('request_initial_state')
def handle_request_initial_state():
    """Handles a client's request for the current game state."""
    logging.info("Received 'request_initial_state' event. Sending current state.")
    broadcast_game_state()

def broadcast_game_state():
    """Captures logs, serializes, and broadcasts the current game state."""
    # Move captured logs into the game state object before serialization
    game.game_state.log_messages = list(list_log_handler.log_records)
    list_log_handler.clear() # Clear the handler for the next batch of logs

    state_dict = game.game_state.to_dict()
    socketio.emit('game_state_update', state_dict)
    logging.info(f"Game state update broadcasted. Phase: {state_dict.get('current_phase')}, Turn: {state_dict.get('current_turn')}")

@socketio.on('start_game')
def handle_start_game():
    """
    Handles the start game event from a client.
    The game is already set up on server start, so this now acts as a way
    to signal readiness and get the initial state, or to start playing.
    In this new flow, we can just advance to the first phase.
    """
    logging.info("Received 'start_game' event. Advancing to the first phase.")
    list_log_handler.clear()
    # The game is already set up, so we just run the first phase
    game.run_next_phase()
    broadcast_game_state()

@socketio.on('next_phase')
def handle_next_phase():
    """Handles the next phase event from a client."""
    logging.info("Received 'next_phase' event.")
    game.run_next_phase()
    broadcast_game_state()

@socketio.on('reset_game')
def handle_reset_game():
    """Handles the reset game event from a client."""
    global game
    logging.info("Received 'reset_game' event. Resetting game state.")
    list_log_handler.clear() # Clear logs
    game = Game(player_names=["玩家一", "玩家二"], assets_path_str="tianji-fix-data-and/assets")
    game.setup() # Setup the new game
    broadcast_game_state() # Broadcast its initial state


if __name__ == '__main__':
    logging.info("Starting Tianji Bian server with Eventlet...")
    # The socketio.run function will use the eventlet server automatically
    # because of the async_mode='eventlet' argument in the SocketIO constructor.
    socketio.run(app, host='0.0.0.0', port=5000)