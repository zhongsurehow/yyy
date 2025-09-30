import logging
import random
from typing import List
from ..game_state import GameState
from ..player import Player
from .. import qimen as qm

# Get the story_logger from the root of the game
story_logger = logging.getLogger("story_logger")

def _trigger_lun_dao(game_instance, challenger: Player, defender: Player):
    """Handles the logic for a duel between two players."""
    story_logger.info(f"--- Lun Dao Duel: {challenger.name} vs {defender.name} ---")

    challenger_cards = [c for c in challenger.hand if c.card_type == 'basic']
    defender_cards = [c for c in defender.hand if c.card_type == 'basic']

    if not challenger_cards or not defender_cards:
        story_logger.info("  - The duel cannot proceed as one or both players lack basic cards.")
        return

    challenger_card = min(challenger_cards, key=lambda c: c.strokes)
    defender_card = min(defender_cards, key=lambda c: c.strokes)

    story_logger.info(f"  - {challenger.name} reveals '{challenger_card.name}' ({challenger_card.strokes} strokes).")
    story_logger.info(f"  - {defender.name} reveals '{defender_card.name}' ({defender_card.strokes} strokes).")

    winner, loser = (None, None)
    if challenger_card.strokes < defender_card.strokes:
        winner, loser = challenger, defender
        story_logger.info(f"  - With fewer strokes, {challenger.name} wins the duel!")
    elif defender_card.strokes < challenger_card.strokes:
        winner, loser = defender, challenger
        story_logger.info(f"  - With fewer strokes, {defender.name} wins the duel!")
    else:
        story_logger.info("  - The strokes are equal, resulting in a draw!")

    if winner:
        amount = min(loser.gold, 5)
        loser.change_resource("gold", -amount)
        winner.change_resource("gold", amount)
        story_logger.info(f"  - {winner.name} takes {amount} gold from {loser.name}.")
        game_instance._check_player_elimination(loser)

    challenger.hand.remove(challenger_card)
    game_instance.game_state.basic_discard_pile.append(challenger_card)
    defender.hand.remove(defender_card)
    game_instance.game_state.basic_discard_pile.append(defender_card)
    story_logger.info("  - The cards used in the duel are discarded.")


def _choose_best_move(game_state: GameState, player: Player, valid_moves: List[str]) -> str:
    """A simple AI to choose the best move for a player."""
    move_scores = {}

    story_logger.info(f"  - {player.name} (at {player.position}) considers where to move.")

    for move in valid_moves:
        score = 0
        zone = game_state.game_board.get_zone(move)
        palace = game_state.game_board.get_palace_for_zone(move)
        gate_name = game_state.game_board.qimen_gates.get(palace)
        gate_info = qm.GATE_EFFECTS.get(gate_name, {})
        reasoning = []

        if zone.department == 'tian':
            if zone.gold_reward > 0:
                score += 5
                reasoning.append(f"it's in the Tian department with a {zone.gold_reward} gold reward")
            else:
                score -= 3
                reasoning.append("it's a stagnant Tian zone")
        elif zone.department == 'di':
            if zone.gold_penalty > 0:
                score -= 5
                reasoning.append(f"it's in the Di department with a {zone.gold_penalty} gold penalty")
            else:
                score += 3
                reasoning.append("it's a Di zone with no penalty")

        if gate_info.get("type") == "Auspicious":
            score += 10
            reasoning.append(f"it has the auspicious '{gate_info.get('name')}' gate")
        elif gate_info.get("type") == "Inauspicious":
            score -= 10
            reasoning.append(f"it has the inauspicious '{gate_info.get('name')}' gate")

        other_players = [p for p in game_state.players if p.position == move and not p.is_eliminated]
        if other_players:
            score -= 7 # Avoid conflict for this simple AI
            reasoning.append(f"it is occupied by {other_players[0].name}")

        move_scores[move] = score
        if reasoning:
            story_logger.info(f"    - Considering {move}: {', '.join(reasoning)}. (Score: {score})")

    if not move_scores:
        return random.choice(valid_moves)

    best_move = max(move_scores, key=move_scores.get)
    story_logger.info(f"  - After weighing the options, {player.name} decides to move to {best_move}.")
    return best_move


def execute(game_instance):
    """
    Executes the logic for the MOVEMENT phase of the game.
    - Players move across the board.
    - Duels (Lun Dao) are triggered.
    - Qi Men Gate effects are triggered.
    """
    game_state = game_instance.game_state
    game_state.set_phase("MOVEMENT")
    story_logger.info("\n--- Movement Phase ---")
    story_logger.info("Players move across the board, triggering events.")

    active_players = [p for p in game_state.players if not p.is_eliminated]

    for player in active_players:
        valid_moves = game_state.game_board.get_valid_moves(player.position)
        if not valid_moves:
            story_logger.info(f"  - {player.name} is at {player.position} and has no valid moves.")
            continue

        destination = _choose_best_move(game_state, player, valid_moves)
        original_position = player.position
        player.position = destination
        story_logger.info(f"  - {player.name} moves from {original_position} to {destination}.")

        other_players_in_zone = [p for p in active_players if p.position == destination and p.player_id != player.player_id]
        if other_players_in_zone:
            defender = other_players_in_zone[0]
            story_logger.info(f"  - This triggers a 'Lun Dao' (duel) with {defender.name}!")
            _trigger_lun_dao(game_instance, player, defender)

    game_instance._trigger_gate_effects()