import random
import logging
import math
from pathlib import Path
from typing import List

from .game_loader import GameLoader
from .game_state import GameState
from .player import Player
from .card import Card
from .effect_engine import EffectEngine
from . import five_elements as fe
from . import qimen as qm
from .solar_term import SOLAR_TERMS_CYCLE
from .phases import (
    time_phase,
    placement_phase,
    movement_phase,
    interpretation_phase,
    resolution_phase,
    upkeep_phase,
)

# Get the logger for the game's narrative story.
# The configuration of this logger is handled in the main application entry point (e.g., server.py).
story_logger = logging.getLogger("story_logger")


class Game:
    """Orchestrates the setup and execution of the game."""

    @property
    def active_players(self) -> List[Player]:
        """Returns a list of players who are not eliminated."""
        return [p for p in self.game_state.players if not p.is_eliminated]

    def __init__(self, player_names: List[str], assets_path_str: str):
        self.game_state = GameState()
        self.player_names = player_names
        self.loader = GameLoader(Path(assets_path_str))
        self.effect_engine = EffectEngine(self.game_state)
        self.phases = [
            ("TIME", lambda: time_phase.execute(self.game_state, self)),
            ("PLACEMENT", lambda: placement_phase.execute(self.game_state)),
            ("MOVEMENT", lambda: movement_phase.execute(self)),
            ("INTERPRETATION", lambda: interpretation_phase.execute(self)),
            ("RESOLUTION", lambda: resolution_phase.execute(self)),
            ("UPKEEP", lambda: upkeep_phase.execute(self)),
        ]
        self.phase_index = 0


    def setup(self):
        """Initializes the game state."""
        logging.info("--- Setting up a new game of Tianji Bian ---")
        story_logger.info("--- Setting up a new game of Tianji Bian ---")

        # Reset game state for a new game
        self.game_state = GameState()
        self.phase_index = 0

        all_decks = self.loader.load_all_cards()
        self.game_state.basic_deck = all_decks.get("basic", [])
        self.game_state.celestial_stem_deck = all_decks.get("celestial_stem", [])
        self.game_state.terrestrial_branch_deck = all_decks.get("terrestrial_branch", [])

        random.shuffle(self.game_state.basic_deck)
        random.shuffle(self.game_state.celestial_stem_deck)
        random.shuffle(self.game_state.terrestrial_branch_deck)

        for i, name in enumerate(self.player_names):
            self.game_state.players.append(Player(player_id=str(i + 1), name=name))

        self.game_state.game_fund = len(self.game_state.players) * 100
        logging.info(f"Game fund initialized to: {self.game_state.game_fund}")

        self._update_qimen_gates()

        ren_zones = [zone.zone_id for zone in self.game_state.game_board.zones.values() if zone.department == 'ren']
        tian_zones = [zone.zone_id for zone in self.game_state.game_board.zones.values() if zone.department == 'tian']

        if ren_zones:
            self.game_state.players[0].position = ren_zones[0]
        if tian_zones and len(self.game_state.players) > 1:
            self.game_state.players[1].position = tian_zones[0]
        if ren_zones and len(self.game_state.players) > 2:
             self.game_state.players[2].position = ren_zones[1]

        for player in self.game_state.players:
            while len(player.hand) < 7:
                self._reshuffle_if_needed('basic')
                if not self.game_state.basic_deck:
                    logging.warning(f"Cannot draw more cards for {player.name}, deck is empty.")
                    break
                player.add_card_to_hand(self.game_state.basic_deck.pop())

        self.game_state.current_phase = "SETUP"
        story_logger.info("Game setup is complete. Players and cards are ready.")

    def run_next_phase(self):
        """
        Executes the next phase of the game. This is the main engine that drives
        the game forward, progressing from one phase to the next and handling
        the start of new rounds.
        """
        # If a winner has been declared or only one player remains, end the game.
        if self.game_state.winner or len(self.active_players) <= 1:
            story_logger.info("Game has ended. No more phases will be run.")
            if not self.game_state.winner:
                self._check_for_winner(10, 10)  # Force end-game check
            return

        # At the start of the phase cycle, begin a new round.
        if self.phase_index == 0:
            self.game_state.current_turn += 1
            story_logger.info(f"\n***** Round {self.game_state.current_turn} *****")

            # After the first round, advance the solar term and update the board.
            if self.game_state.current_turn > 1:
                self.game_state.solar_term_index = (self.game_state.solar_term_index + 1) % len(SOLAR_TERMS_CYCLE)
                story_logger.info(f"*** New Solar Term: {self.game_state.current_solar_term.name} ({self.game_state.dun_type.value} Dun). ***")
                self._update_qimen_gates()

            # Resolve any effects that trigger at the start of a turn.
            self._resolve_delayed_effects("NEXT_TURN_START")

        # Get and execute the current phase from the list.
        phase_name, phase_method = self.phases[self.phase_index]
        self.game_state.current_phase = phase_name

        story_logger.info(f"\n--- Starting {phase_name} Phase ---")
        if phase_name.upper() in self.game_state.skipped_phases:
            story_logger.info(f"--- Skipping {phase_name} Phase (Effect active) ---")
        else:
            phase_method()

        # Advance the phase index, looping back to 0 after the last phase.
        self.phase_index = (self.phase_index + 1) % len(self.phases)

        # Check for a winner after every phase.
        self._check_for_winner(self.game_state.current_turn, 10) # Assuming 10 rounds max for now

    def _check_for_winner(self, current_round: int, max_rounds: int) -> Player | None:
        """
        Checks for victory conditions. The game can end in one of three ways:
        1. One player is left standing.
        2. All players are eliminated (draw).
        3. The round limit is reached (winner decided by wealth).
        """
        if self.game_state.winner:  # If winner is already declared, do nothing.
            return self.game_state.winner

        winner = None
        # 1. Last player standing
        if len(self.active_players) == 1:
            winner = self.active_players[0]
            story_logger.info(f"\n!!! VICTORY: {winner.name} is the last player standing! !!!")
        # 2. All players eliminated
        elif len(self.active_players) == 0:
            story_logger.info("\n!!! DRAW: All players have been eliminated. !!!")
            self.game_state.winner = "DRAW"
            return None
        # 3. Round limit reached (checked only at the end of a round)
        elif current_round >= max_rounds and self.phase_index == 0:
            story_logger.info(f"\n--- Game has reached the round limit of {max_rounds}. Calculating winner by wealth... ---")
            # Sort players by gold, then by health, to find the wealthiest.
            potential_winners = sorted(self.active_players, key=lambda p: (p.gold, p.health), reverse=True)
            if not potential_winners:
                story_logger.info("\n!!! DRAW: No active players left to determine a winner. !!!")
                self.game_state.winner = "DRAW"
                return None
            winner = potential_winners[0]
            story_logger.info(f"  - {winner.name} has the most wealth (Gold: {winner.gold}, Health: {winner.health}).")
            story_logger.info(f"\n!!! VICTORY: {winner.name} wins by having the most wealth! !!!")

        if winner:
            self.game_state.winner = winner
        return winner

    def _resolve_delayed_effects(self, trigger_moment: str):
        """Resolves any delayed effects that match the current game moment."""
        story_logger.info(f"--- Checking for delayed effects at {trigger_moment} ---")

        effects_to_trigger = [
            item for item in self.game_state.delayed_effects
            if item.get("delay") == trigger_moment
        ]

        for item in effects_to_trigger:
            self.game_state.delayed_effects.remove(item)

        if not effects_to_trigger:
            return

        story_logger.info(f"  - Triggering {len(effects_to_trigger)} delayed effect(s).")
        for item in effects_to_trigger:
            self.effect_engine.queue_effect(item["effect"], item["source_player"])

        self.effect_engine.resolve_effects()

    def _trigger_gate_effects(self):
        """Triggers the Qi Men gate effects for all players based on their current position."""
        story_logger.info("--- Triggering Qi Men Gate Effects ---")
        for player in self.active_players:
            palace = self.game_state.game_board.get_palace_for_zone(player.position)
            if not palace: continue

            gate_name = self.game_state.game_board.qimen_gates.get(palace)
            if gate_name:
                gate_info = qm.GATE_EFFECTS.get(gate_name, {})
                gate_display_name = gate_info.get("name", gate_name)
                story_logger.info(f"  - {player.name} is in {palace.upper()} Palace, triggering the '{gate_display_name}' gate.")
                
                gate_effect = qm.get_effect_for_gate(gate_name)
                if gate_effect:
                    self.effect_engine.queue_effect(gate_effect, player)

        self.effect_engine.resolve_effects()
        for player in self.active_players: self._check_player_elimination(player)

    def _update_qimen_gates(self):
        """Updates the gate layout on the board based on the current solar term."""
        dun_type = self.game_state.dun_type
        ju_number = qm.get_ju_number_for_solar_term(self.game_state.solar_term_index, dun_type)
        gate_layout = qm.get_gate_layout_for_ju(ju_number, dun_type)
        if gate_layout:
            self.game_state.game_board.qimen_gates = gate_layout
            story_logger.info(f"The Qi Men gates have shifted for {dun_type} Dun Ju {ju_number}.")
        else:
            logging.error(f"Could not find gate layout for {dun_type} Dun Ju {ju_number}")
        
    def _check_player_elimination(self, player: Player):
        """Checks if a player should be eliminated and updates their status."""
        if player.is_eliminated: return
        if player.health <= 0:
            player.is_eliminated = True
            story_logger.warning(f"!!! PLAYER ELIMINATED: {player.name} has been eliminated due to low health. !!!")

    def _get_deck_and_discard(self, deck_type: str) -> (List[Card], List[Card]):
        gs = self.game_state
        if deck_type == 'basic': return gs.basic_deck, gs.basic_discard_pile
        elif deck_type == 'function': return gs.function_deck, gs.function_discard_pile
        elif deck_type == 'celestial_stem': return gs.celestial_stem_deck, gs.celestial_stem_discard_pile
        elif deck_type == 'terrestrial_branch': return gs.terrestrial_branch_deck, gs.terrestrial_branch_discard_pile
        logging.warning(f"Unknown deck type requested: {deck_type}")
        return None, None

    def _reshuffle_if_needed(self, deck_type: str):
        deck, discard_pile = self._get_deck_and_discard(deck_type)
        if deck is None: return

        if not deck:
            if len(discard_pile) > 0:
                story_logger.info(f"The '{deck_type}' deck is empty. Reshuffling the discard pile.")
                deck.extend(discard_pile)
                random.shuffle(deck)
                discard_pile.clear()
            else:
                logging.warning(f"Deck '{deck_type}' and its discard pile are both empty.")