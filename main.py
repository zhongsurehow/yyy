import logging
from src.game import Game

def setup_logging():
    """Configures logging for the application."""
    # Configure the root logger
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

    # Get the story logger and set its level
    story_logger = logging.getLogger("story_logger")
    story_logger.setLevel(logging.INFO)

    # Prevent story_logger from propagating to the root logger to avoid duplicate messages
    story_logger.propagate = False

    # If the story logger doesn't have handlers, add a new one.
    if not story_logger.handlers:
        handler = logging.StreamHandler()
        # Use a simple formatter for the story output
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        story_logger.addHandler(handler)

def main():
    """
    Main entry point for running a simulation of the Tianji Bian game engine.
    """
    setup_logging()

    story_logger = logging.getLogger("story_logger")

    story_logger.info("=============================================")
    story_logger.info("===   Tianji Bian - Tutorial Simulation   ===")
    story_logger.info("=============================================")

    try:
        player_names = ["Player 1 (Alice)", "Player 2 (Bob)"]
        assets_path = "tianji-fix-data-and/assets"

        # Define a specific scenario to test for a more controlled tutorial
        test_cards_to_play = ["basic_14_da_you", "basic_21_shi_he"]

        game = Game(player_names=player_names, assets_path_str=assets_path)
        game.setup(test_cards=test_cards_to_play)

        story_logger.info("\n--- Initial Player States ---")
        for p in game.game_state.players:
            story_logger.info(f"  - {p}")

        # Run the simulation for a single, illustrative round
        game.run_game(num_rounds=1)

    except FileNotFoundError as e:
        story_logger.error(f"\nFATAL ERROR: {e}. Make sure the assets directory exists at '{assets_path}'.")
    except Exception as e:
        story_logger.error(f"\nAn unexpected error occurred during the simulation: {e}", exc_info=True)

if __name__ == '__main__':
    main()