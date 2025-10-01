import logging
from ..game_state import GameState

# Get the story_logger from the root of the game
story_logger = logging.getLogger("story_logger")

def execute(game_state: GameState):
    """
    Begins the PLACEMENT phase of the game.
    This phase sets the game state and then waits for player input from the UI.
    The actual card playing is handled by a 'play_card' event from the client.
    """
    game_state.set_phase("PLACEMENT")
    story_logger.info("\n--- Placement Phase ---")
    story_logger.info("Players may now play a card from their hand.")