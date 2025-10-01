import unittest
import logging
from unittest.mock import patch

from src.game import Game
from src.player import Player
from src.card import Card

class TestPlacementPhase(unittest.TestCase):

    def setUp(self):
        """Set up a new game instance and players for each test."""
        logging.basicConfig(level=logging.WARNING)
        self.assets_path = "tianji-fix-data-and/assets"
        self.game = Game(player_names=["Alice", "Bob"], assets_path_str=self.assets_path)
        self.game.setup()

        self.alice = self.game.game_state.get_player("1")
        self.bob = self.game.game_state.get_player("2")

        # Give Alice a predictable card with a known effect for testing
        self.test_card = Card(
            card_id="test_effect_card",
            name="Test Card",
            card_type="function",
            description="A test card.",
            effect={"actions": [{"action": "GAIN_RESOURCE", "params": {"target": "SELF", "resource": "gold", "value": 20}}]}
        )
        self.alice.hand.append(self.test_card)

    def test_play_card_successfully(self):
        """Tests that a player can successfully play a card during the Placement Phase."""
        # --- ARRANGE ---
        self.game.game_state.set_phase("PLACEMENT")
        initial_gold = self.alice.gold
        initial_hand_size = len(self.alice.hand)
        initial_discard_size = len(self.game.game_state.function_discard_pile)

        # --- ACT ---
        self.game.play_card(player_id=self.alice.player_id, card_id=self.test_card.card_id)

        # --- ASSERT ---
        # 1. Check that the card's effect was applied.
        self.assertEqual(self.alice.gold, initial_gold + 20)
        # 2. Check that the card was removed from the player's hand.
        self.assertEqual(len(self.alice.hand), initial_hand_size - 1)
        self.assertNotIn(self.test_card, self.alice.hand)
        # 3. Check that the card was added to the correct discard pile.
        self.assertEqual(len(self.game.game_state.function_discard_pile), initial_discard_size + 1)
        self.assertIn(self.test_card, self.game.game_state.function_discard_pile)

    def test_play_card_wrong_phase(self):
        """Tests that a player cannot play a card outside of the Placement Phase."""
        # --- ARRANGE ---
        # The phase is "SETUP" by default after setup()
        initial_gold = self.alice.gold
        initial_hand_size = len(self.alice.hand)

        # --- ACT ---
        self.game.play_card(player_id=self.alice.player_id, card_id=self.test_card.card_id)

        # --- ASSERT ---
        # Assert that the game state has NOT changed.
        self.assertEqual(self.alice.gold, initial_gold)
        self.assertEqual(len(self.alice.hand), initial_hand_size)

    def test_play_card_not_in_hand(self):
        """Tests that a player cannot play a card they do not have."""
        # --- ARRANGE ---
        self.game.game_state.set_phase("PLACEMENT")
        initial_gold = self.alice.gold
        initial_hand_size = len(self.alice.hand)

        # --- ACT ---
        self.game.play_card(player_id=self.alice.player_id, card_id="non_existent_card")

        # --- ASSERT ---
        # Assert that the game state has NOT changed.
        self.assertEqual(self.alice.gold, initial_gold)
        self.assertEqual(len(self.alice.hand), initial_hand_size)

if __name__ == '__main__':
    unittest.main()