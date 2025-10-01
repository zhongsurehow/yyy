import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

from .card import Card
from .player import Player
from .game_board import GameBoard
from .solar_term import SolarTerm, SOLAR_TERMS_CYCLE, DunType

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
    solar_term_index: int = 0
    current_turn: int = 0
    current_phase: str = "SETUP" # e.g., SETUP, TIME, PLACEMENT, MOVEMENT, etc.
    active_player_index: int = 0
    starting_player_index: int = 0  # Track which player started the current Ju
    winner: Any = None # Can be a Player object or "DRAW"
    log_messages: List[str] = field(default_factory=list)

    @property
    def current_solar_term(self) -> SolarTerm:
        """Returns the current SolarTerm object."""
        return SOLAR_TERMS_CYCLE[self.solar_term_index]

    @property
    def dun_type(self) -> DunType:
        """Returns the Dun type ('YANG' or 'YIN') for the current solar term."""
        return self.current_solar_term.dun

    # Rule and effect tracking
    active_rules: Dict[str, Any] = field(default_factory=dict)
    last_resolved_effect: Dict[str, Any] | None = None
    interrupt_flags: Dict[str, bool] = field(default_factory=dict)
    effect_queue: List[Dict[str, Any]] = field(default_factory=list)
    delayed_effects: List[Dict[str, Any]] = field(default_factory=list)
    skipped_phases: set = field(default_factory=set) # For phases to be skipped this round

    # World state
    entities: Dict[str, Any] = field(default_factory=dict) # For traps, beacons, etc. keyed by a unique ID

    def get_player(self, player_id: str) -> Player | None:
        """Finds a player by their ID."""
        return next((p for p in self.players if p.player_id == player_id), None)

    def get_active_player(self) -> Player:
        """Returns the player whose turn it is."""
        return self.players[self.active_player_index]

    def set_phase(self, phase_name: str):
        """Sets the current game phase."""
        self.current_phase = phase_name
        logging.info(f"== Phase: {phase_name} ==")

    def __repr__(self) -> str:
        return f"GameState(Turn={self.current_turn}, Phase='{self.current_phase}', ActivePlayer='{self.get_active_player().name}')"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the entire GameState object to a dictionary."""
        active_player = self.get_active_player() if self.players else None
        winner_dict = None
        if self.winner:
            if isinstance(self.winner, Player):
                winner_dict = self.winner.to_dict()
            else: # Draw
                winner_dict = self.winner

        return {
            "players": [p.to_dict() for p in self.players],
            "game_board": self.game_board.to_dict(),
            "current_turn": self.current_turn,
            "current_phase": self.current_phase,
            "active_player_id": active_player.player_id if active_player else None,
            "solar_term": self.current_solar_term.name,
            "dun_type": self.dun_type.value,
            "game_fund": self.game_fund,
            "current_celestial_stem": self.current_celestial_stem.to_dict() if self.current_celestial_stem else None,
            "current_terrestrial_branch": self.current_terrestrial_branch.to_dict() if self.current_terrestrial_branch else None,
            "log_messages": self.log_messages,
            "winner": winner_dict,
        }