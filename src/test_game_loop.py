import unittest
import logging
from unittest.mock import patch

from src.game import Game
from src.player import Player
from src.card import Card
from src.phases import time_phase, resolution_phase

class TestGameLoop(unittest.TestCase):

    def setUp(self):
        """Set up a new game instance for each test."""
        # Suppress noisy logs for cleaner test output, can be set to INFO for debugging
        logging.basicConfig(level=logging.WARNING)

        # We need a path to the assets directory to load card data
        # Assuming the test is run from the root directory
        self.assets_path = "tianji-fix-data-and/assets"
        self.game = Game(player_names=["Alice", "Bob"], assets_path_str=self.assets_path)
        self.game.setup()

        # For predictable testing, manually set player states
        self.alice = self.game.game_state.get_player("1")
        self.bob = self.game.game_state.get_player("2")
        self.alice.gold = 50
        self.bob.gold = 50

        # Place Alice in a Tian zone and Bob in a Di zone for the resolution phase test
        self.alice.position = "li_tian" # Li palace is 'fire'
        self.bob.position = "kan_di"   # Kan palace is 'water'

    def test_time_and_resolution_phase(self):
        """
        Tests if the Time Phase correctly sets rewards/penalties and
        if the Resolution Phase correctly applies them.
        """
        # --- TIME PHASE ---
        # Manually set Gan-Zhi to get a predictable outcome.
        # Stem: Jia (wood) -> generates Fire (离), overcomes Earth (坤, 艮)
        # Branch: Zi (water) -> generates Wood (震, 巽), overcomes Fire (离)
        # Beneficial for: Fire, Wood. Harmful for: Earth, Fire.
        # Li (fire) is both beneficial and harmful. For Tian bu, harmful (stagnation) wins.
        # Kan (water) is neutral.

        # Correctly populate the decks before calling the phase method
        # This prevents the "deck is empty" error.
        stem_card = Card(card_id="celestial_stem_jia", name="甲", card_type="celestial_stem")
        branch_card = Card(card_id="terrestrial_branch_zi", name="子", card_type="terrestrial_branch")
        self.game.game_state.celestial_stem_deck.append(stem_card)
        self.game.game_state.terrestrial_branch_deck.append(branch_card)

        time_phase.execute(self.game.game_state, self.game)

        li_tian_zone = self.game.game_state.game_board.get_zone("li_tian")
        kan_di_zone = self.game.game_state.game_board.get_zone("kan_di")

        # Assertions for Time Phase logic
        # li_tian is fire. fire is beneficial (wood->fire) and harmful (water->fire). Harmful wins, so reward is 0.
        self.assertEqual(li_tian_zone.gold_reward, 0)
        # kan_di is water, which is neutral in this case. Penalty should be 0.
        self.assertEqual(kan_di_zone.gold_penalty, 0)

        # --- RESOLUTION PHASE ---
        initial_alice_gold = self.alice.gold
        initial_bob_gold = self.bob.gold

        resolution_phase.execute(self.game)

        # Assertions for Resolution Phase logic
        self.assertEqual(self.alice.gold, initial_alice_gold + li_tian_zone.gold_reward)
        self.assertEqual(self.bob.gold, initial_bob_gold - kan_di_zone.gold_penalty)

    def test_qimen_gate_trigger_yang_and_yin_dun(self):
        """
        Tests if moving into a palace with a Qi Men gate correctly triggers its effect
        for both Yang and Yin Dun cycles.
        """
        # --- YANG DUN TEST ---
        # setup() initializes the game to solar_term_index 0 (冬至, Yang Dun).
        # This corresponds to Yang Ju 1. In Yang Ju 1, Kan palace has 休门 (Rest Gate).
        # 休门 gives +10 health.

        # Ensure gates are set for the initial state (setup() already calls this)
        self.game._update_qimen_gates()

        # Manually move Bob to a Di zone in the Kan palace
        self.bob.position = "kan_di"
        initial_bob_health = self.bob.health

        # Trigger gate effects
        self.game._trigger_gate_effects()

        # Assert that the Yang Dun gate effect was applied
        self.assertEqual(self.bob.health, initial_bob_health + 10)

        # --- YIN DUN TEST ---
        # Now, advance to a Yin Dun solar term and test again.
        # We'll set the solar term to 13 ("小暑"), which corresponds to Yin Ju 8.
        # In Yin Ju 8, the Kan palace has the 开门 (Open Gate), which gives +5 gold.
        self.game.game_state.solar_term_index = 13
        self.game._update_qimen_gates() # Force update for the new solar term

        # Reset Bob's health to avoid confusion from the previous test part
        self.bob.health = initial_bob_health
        initial_bob_gold = self.bob.gold

        # Bob is already in "kan_di", so we just trigger the effects again.
        self.game._trigger_gate_effects()

        # Assert that the Yin Dun gate effect was applied
        self.assertEqual(self.bob.gold, initial_bob_gold + 5)
        # Assert that health did not change this time
        self.assertEqual(self.bob.health, initial_bob_health)

if __name__ == '__main__':
    unittest.main()