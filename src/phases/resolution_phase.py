import logging
import math
from ..game_state import GameState

# Get the story_logger from the root of the game
story_logger = logging.getLogger("story_logger")

def execute(game_instance):
    """
    Executes the logic for the RESOLUTION phase of the game.
    - Calculates and applies rewards and penalties from board positions.
    """
    game_state = game_instance.game_state
    game_state.set_phase("RESOLUTION")
    story_logger.info("\n--- Resolution Phase ---")
    story_logger.info("Rewards and penalties from board positions are calculated.")

    active_players = [p for p in game_state.players if not p.is_eliminated]

    for player in active_players:
        zone = game_state.game_board.get_zone(player.position)
        if not zone: continue

        if zone.department == 'tian':
            reward = zone.gold_reward
            if reward > 0:
                player.change_resource("gold", reward)
                game_state.game_fund -= reward
                story_logger.info(f"  - {player.name} is in a Tian zone and gains {reward} gold.")
            else:
                story_logger.info(f"  - {player.name} is in a stagnant Tian zone and gains no reward.")
        elif zone.department == 'di':
            penalty = zone.gold_penalty
            if penalty > 0:
                paid_amount = min(player.gold, penalty)
                player.change_resource("gold", -paid_amount)
                game_state.game_fund += paid_amount
                story_logger.info(f"  - {player.name} is in a Di zone and pays a penalty of {paid_amount} gold.")
        elif zone.department == 'zhong':
            penalty = math.ceil(player.gold * 0.10)
            player.change_resource("gold", -penalty)
            game_state.game_fund += penalty
            story_logger.info(f"  - {player.name} is in the Zhong Gong and pays a 10% tax of {penalty} gold.")

    for player in active_players:
        game_instance._check_player_elimination(player)