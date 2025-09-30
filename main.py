import logging
import json
from src.game import Game

def setup_logging():
    """Configures logging for the application."""
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    story_logger = logging.getLogger("story_logger")
    story_logger.setLevel(logging.INFO)
    story_logger.propagate = False
    if not story_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        story_logger.addHandler(handler)

def load_config() -> dict:
    """Loads the configuration from config.json."""
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("FATAL: config.json not found. Please ensure it exists in the root directory.")
        return None
    except json.JSONDecodeError:
        logging.error("FATAL: Could not parse config.json. Please check for syntax errors.")
        return None

def main():
    """
    Main entry point for running a simulation of the Tianji Bian game engine.
    """
    setup_logging()
    story_logger = logging.getLogger("story_logger")

    config = load_config()
    if not config:
        return

    sim_config = config.get("simulation", {})

    story_logger.info("=============================================")
    story_logger.info("===   Tianji Bian - Tutorial Simulation   ===")
    story_logger.info("=============================================")

    try:
        player_names = sim_config.get("player_names", ["Player 1", "Player 2"])
        num_rounds = sim_config.get("num_rounds", 10)
        test_cards = sim_config.get("test_cards", [])
        assets_path = "tianji-fix-data-and/assets"

        game = Game(player_names=player_names, assets_path_str=assets_path)
        game.setup(test_cards=test_cards)

        story_logger.info("\n--- Initial Player States ---")
        for p in game.game_state.players:
            story_logger.info(f"  - {p}")

        game.run_game(num_rounds=num_rounds)

    except FileNotFoundError as e:
        story_logger.error(f"\nFATAL ERROR: {e}. Make sure the assets directory exists at '{assets_path}'.")
    except Exception as e:
        story_logger.error(f"\nAn unexpected error occurred during the simulation: {e}", exc_info=True)

if __name__ == '__main__':
    main()