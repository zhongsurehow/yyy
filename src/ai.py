import logging
import random
from typing import List

from .game_state import GameState
from .player import Player
from . import qimen as qm

# Get the story_logger from the root of the game
story_logger = logging.getLogger("story_logger")

def choose_best_move(game_state: GameState, player: Player, valid_moves: List[str]) -> str:
    """A simple AI to choose the best move for a player."""
    move_scores = {}

    story_logger.info(f"  - {player.name} (at {player.position}) considers where to move.")

    for move in valid_moves:
        score = 0
        zone = game_state.game_board.get_zone(move)
        palace = game_state.game_board.get_palace_for_zone(move)

        # Correctly get gate info from the detailed gate structure
        gate_data = game_state.game_board.qimen_gates.get(palace, {})
        gate_type = gate_data.get("type")
        gate_name_for_log = gate_data.get("name")
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

        if gate_type == "Auspicious":
            score += 10
            reasoning.append(f"it has the auspicious '{gate_name_for_log}' gate")
        elif gate_type == "Inauspicious":
            score -= 10
            reasoning.append(f"it has the inauspicious '{gate_name_for_log}' gate")

        other_players = [p for p in game_state.players if p.position == move and not p.is_eliminated]
        if other_players:
            score -= 7 # Avoid conflict for this simple AI
            reasoning.append(f"it is occupied by {other_players[0].name}")

        move_scores[move] = score
        if reasoning:
            story_logger.info(f"    - Considering {move}: {', '.join(reasoning)}. (Score: {score})")

    if not move_scores:
        if not valid_moves: return None
        best_move = random.choice(valid_moves)
        story_logger.info(f"  - With no clear preference, {player.name} randomly chooses to move to {best_move}.")
        return best_move

    best_move = max(move_scores, key=move_scores.get)
    story_logger.info(f"  - After weighing the options, {player.name} decides to move to {best_move}.")
    return best_move