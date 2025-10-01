import unittest
import logging
from unittest.mock import patch

from src.game import Game
from src.player import Player
from src.phases import movement_phase

class TestGameRules(unittest.TestCase):

    def setUp(self):
        """Set up a new game instance for each test."""
        # Suppress noisy logs for cleaner test output
        logging.basicConfig(level=logging.WARNING)

        self.assets_path = "tianji-fix-data-and/assets"
        self.game = Game(player_names=["Alice", "Bob"], assets_path_str=self.assets_path)
        self.game.setup()

        self.alice = self.game.game_state.get_player("1")
        self.bob = self.game.game_state.get_player("2")
        self.alice.health = 100
        self.bob.health = 100
        self.alice.position = "li_tian" # Start Alice in a known position

    @patch('src.ai.choose_best_move')
    def test_movement_phase_triggers_gate_effect(self, mock_choose_move):
        """
        Tests that a player moving into a new palace during the movement phase
        correctly triggers the effect of the Qi Men gate in that palace.
        """
        # --- ARRANGE ---
        # In the initial state (Yang Dun, Ju 1), the 'kan' palace has the '休门' (Rest Gate),
        # which should grant +10 health.

        # We mock the AI's choice to force Alice to move into the 'kan' palace.
        # We must also provide a return value for Bob's move, as the phase loops over all players.
        alice_destination = "kan_di"
        # Bob starts at li_tian, so li_ren is a valid move.
        bob_destination = "li_ren"
        mock_choose_move.side_effect = [alice_destination, bob_destination]

        initial_health = self.alice.health

        # --- ACT ---
        # Execute the entire movement phase. This will involve the AI choice,
        # the player's move, and the triggering of gate effects.
        movement_phase.execute(self.game)

        # --- ASSERT ---
        # 1. Assert that Alice's position and health were updated correctly.
        self.assertEqual(self.alice.position, alice_destination)
        self.assertEqual(self.alice.health, initial_health + 10)

        # 2. Assert that Bob's position was also updated.
        self.assertEqual(self.bob.position, bob_destination)

        # 3. Assert that the mock was called for both players.
        self.assertEqual(mock_choose_move.call_count, 2)


if __name__ == '__main__':
    unittest.main()