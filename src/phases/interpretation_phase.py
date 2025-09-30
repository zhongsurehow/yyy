import logging
from ..game_state import GameState
from ..player import Player

# Get the story_logger from the root of the game
story_logger = logging.getLogger("story_logger")

def execute(game_instance):
    """
    Executes the logic for the INTERPRETATION phase of the game.
    - Players reveal their placed cards.
    - Card effects are queued and resolved based on board order.
    """
    game_state = game_instance.game_state
    effect_engine = game_instance.effect_engine

    game_state.set_phase("INTERPRETATION")
    story_logger.info("\n--- Interpretation Phase ---")
    story_logger.info("Players reveal their cards and effects are triggered based on board order.")

    active_players = [p for p in game_state.players if not p.is_eliminated]
    players_with_cards = [p for p in active_players if p.played_card]

    department_priority = {"tian": 0, "ren": 1, "di": 2, "zhong": 99}
    def get_interpretation_sort_key(player: Player):
        zone = game_state.game_board.get_zone(player.position)
        if not zone: return (99, 99)
        return (zone.luoshu_number, department_priority.get(zone.department, 99))

    players_with_cards.sort(key=get_interpretation_sort_key)

    for player in players_with_cards:
        card = player.played_card
        story_logger.info(f"  - {player.name} (at {player.position}) reveals '{card.name}'.")
        player_zone = game_state.game_board.get_zone(player.position)
        if not player_zone: continue

        variant_key = player_zone.department
        variant_effect = card.core_mechanism.get("variants", {}).get(variant_key, {}).get("effect")
        effect_to_queue = variant_effect if variant_effect else card.effect

        if effect_to_queue:
            effect_engine.queue_effect(effect_to_queue, player)
        else:
            logging.warning(f"Card {card.name} has no valid effect for department '{variant_key}'.")

    effect_engine.resolve_effects()
    for player in active_players:
        game_instance._check_player_elimination(player)