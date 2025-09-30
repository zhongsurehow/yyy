import logging
from ..game_state import GameState

# Get the story_logger from the root of the game
story_logger = logging.getLogger("story_logger")

def execute(game_instance):
    """
    Executes the logic for the UPKEEP phase of the game.
    - Resolves delayed effects.
    - Ticks down status effect durations.
    - Discards used cards.
    - Resets round-specific states.
    - Advances to the next player.
    """
    game_state = game_instance.game_state
    game_state.set_phase("UPKEEP")
    story_logger.info("\n--- Upkeep Phase ---")

    game_instance._resolve_delayed_effects("NEXT_UPKEEP_PHASE")

    active_players = [p for p in game_state.players if not p.is_eliminated]

    for player in active_players:
        player.tick_statuses()
        if player.played_card:
            game_state.basic_discard_pile.append(player.played_card)
            player.played_card = None
    story_logger.info("  - Players discard used cards and status effects are updated.")

    # Reset any round-specific states
    game_state.skipped_phases.clear()
    story_logger.info("  - Round-specific effects (like skipped phases) are now reset.")

    game_state.advance_to_next_player()
    story_logger.info(f"  - The turn passes to the next player: {game_state.get_active_player().name}.")