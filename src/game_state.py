import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

from .card import Card
from .player import Player
from .game_board import GameBoard

@dataclass
class GameState:
    """Manages the entire state of the game."""
    players: List[Player] = field(default_factory=list)
    game_board: GameBoard = field(default_factory=GameBoard)

    # Deck piles
    basic_deck: List[Card] = field(default_factory=list)
    function_deck: List[Card] = field(default_factory=list)
    destiny_deck: List[Card] = field(default_factory=list)
    celestial_stem_deck: List[Card] = field(default_factory=list)
    terrestrial_branch_deck: List[Card] = field(default_factory=list)

    # Discard piles
    basic_discard_pile: List[Card] = field(default_factory=list)
    function_discard_pile: List[Card] = field(default_factory=list)
    celestial_stem_discard_pile: List[Card] = field(default_factory=list)
    terrestrial_branch_discard_pile: List[Card] = field(default_factory=list)

    # Game flow & state
    game_fund: int = 0
    current_celestial_stem: Card | None = None
    current_terrestrial_branch: Card | None = None
    ju_number: int = 1
    current_turn: int = 1
    current_phase: str = "SETUP" # e.g., SETUP, TIME, PLACEMENT, MOVEMENT, etc.
    active_player_index: int = 0
    starting_player_index: int = 0  # Track which player started the current Ju

    # Rule and effect tracking
    active_rules: Dict[str, Any] = field(default_factory=dict)
    last_resolved_effect: Dict[str, Any] | None = None
    interrupt_flags: Dict[str, bool] = field(default_factory=dict)
    effect_queue: List[Dict[str, Any]] = field(default_factory=list)

    def get_player(self, player_id: str) -> Player | None:
        """Finds a player by their ID."""
        return next((p for p in self.players if p.player_id == player_id), None)

    def get_active_player(self) -> Player:
        """Returns the player whose turn it is."""
        return self.players[self.active_player_index]

    def advance_to_next_player(self):
        """Advances the turn to the next player. Increments Ju when all players have been starting player."""
        self.active_player_index = (self.active_player_index + 1) % len(self.players)
        
        # Check if we've completed a full cycle of starting players
        if self.active_player_index == self.starting_player_index:
            # All players have been starting player once - advance Ju
            self.ju_number += 1
            self.starting_player_index = self.active_player_index  # Reset for next Ju
            logging.info(f"*** New Ju: {self.ju_number}. Qi Men Gates will shift. ***")
        
        # Always increment turn when we complete a full player cycle
        if self.active_player_index == 0:
            self.current_turn += 1
            logging.info(f"--- Starting Round {self.current_turn} ---")

    def set_phase(self, phase_name: str):
        """Sets the current game phase."""
        self.current_phase = phase_name
        logging.info(f"== Phase: {phase_name} ==")

    def __repr__(self) -> str:
        return f"GameState(Turn={self.current_turn}, Phase='{self.current_phase}', ActivePlayer='{self.get_active_player().name}')"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the entire GameState object to a dictionary."""
        return {
            "players": [p.to_dict() for p in self.players],
            "game_board": self.game_board.to_dict(),
            "current_turn": self.current_turn,
            "current_phase": self.current_phase,
            "active_player_id": self.get_active_player().player_id,
            "ju_number": self.ju_number,
            "game_fund": self.game_fund,
            "current_celestial_stem": self.current_celestial_stem.to_dict() if self.current_celestial_stem else None,
            "current_terrestrial_branch": self.current_terrestrial_branch.to_dict() if self.current_terrestrial_branch else None,
        }