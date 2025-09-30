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

# Setup a dedicated logger for the game's narrative story
story_logger = logging.getLogger("story_logger")
story_logger.setLevel(logging.INFO)
story_logger.propagate = False
if not story_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    story_logger.addHandler(handler)


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

    def setup(self, test_cards: List[str] = None):
        """Initializes the game state, with an option to inject specific test cards."""
        logging.info("--- Setting up a new game of Tianji Bian ---")

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

        if test_cards:
            for i, player in enumerate(self.game_state.players):
                if i < len(test_cards):
                    card_id_to_find = test_cards[i]
                    test_card = next((c for c in self.game_state.basic_deck if c.card_id == card_id_to_find), None)
                    if test_card:
                        player.add_card_to_hand(test_card)
                        self.game_state.basic_deck.remove(test_card)

        for player in self.game_state.players:
            while len(player.hand) < 7:
                self._reshuffle_if_needed('basic')
                if not self.game_state.basic_deck:
                    logging.warning(f"Cannot draw more cards for {player.name}, deck is empty.")
                    break
                player.add_card_to_hand(self.game_state.basic_deck.pop())

        story_logger.info("Game setup is complete. Players and cards are ready.")

    def run_game(self, num_rounds: int = 1):
        """Runs the main game loop for a specified number of rounds."""
        story_logger.info(f"\n--- Starting Game Simulation ({num_rounds} round(s)) ---")
        logging.info(f"--- Starting Game Run ({num_rounds} round(s)) ---")

        for i in range(1, num_rounds + 1):
            self.run_round(i)

        story_logger.info("\n--- Simulation Finished ---")
        story_logger.info("Final Player States:")
        for player in self.game_state.players:
            story_logger.info(f"  - {player}")
        logging.info("--- Game Run Finished ---")

    def run_round(self, round_number: int):
        """Executes all phases for a single round of the game."""
        if len(self.active_players) <= 1:
            story_logger.info("Not enough active players to continue. Ending game.")
            return

        self.game_state.current_turn = round_number
        story_logger.info(f"\n***** Round {self.game_state.current_turn} *****")

        self._execute_time_phase()
        self._execute_placement_phase()
        self._execute_movement_phase()
        self._execute_interpretation_phase()
        self._execute_resolution_phase()
        self._execute_upkeep_phase()

    def _execute_time_phase(self):
        self.game_state.set_phase("TIME")
        dun_type = self.game_state.dun_type
        dun_text = "Yang" if dun_type == "YANG" else "Yin"
        solar_term_name = self.game_state.current_solar_term.name
        ju_number = qm.get_ju_number_for_solar_term(self.game_state.solar_term_index, dun_type)

        story_logger.info(f"\n--- Time Phase ---")
        story_logger.info(f"The celestial energies shift. It is now the '{solar_term_name}' solar term.")
        story_logger.info(f"This is a {dun_text} Dun period, corresponding to Ju {ju_number}.")
        logging.info(f"当前节气: {solar_term_name} ({dun_text}遁), 第{ju_number}局")

        self._update_qimen_gates()

        if self.game_state.current_celestial_stem:
            logging.info(f"弃置天干牌: {self.game_state.current_celestial_stem.name}")
            self.game_state.celestial_stem_discard_pile.append(self.game_state.current_celestial_stem)
        if self.game_state.current_terrestrial_branch:
            logging.info(f"弃置地支牌: {self.game_state.current_terrestrial_branch.name}")
            self.game_state.terrestrial_branch_discard_pile.append(self.game_state.current_terrestrial_branch)

        self._reshuffle_if_needed('celestial_stem')
        self._reshuffle_if_needed('terrestrial_branch')

        if not self.game_state.celestial_stem_deck or not self.game_state.terrestrial_branch_deck:
            logging.error("Critical: Cannot draw new time cards. Decks are empty.")
            return

        self.game_state.current_celestial_stem = self.game_state.celestial_stem_deck.pop()
        self.game_state.current_terrestrial_branch = self.game_state.terrestrial_branch_deck.pop()
        story_logger.info(f"The new time cards are '{self.game_state.current_celestial_stem.name}' and '{self.game_state.current_terrestrial_branch.name}'.")

        stem_element = fe.get_element_for_stem(self.game_state.current_celestial_stem.card_id.split('_')[-1])
        branch_element = fe.get_element_for_branch(self.game_state.current_terrestrial_branch.card_id.split('_')[-1])

        beneficial_elements = {fe.get_generated_element(stem_element), fe.get_generated_element(branch_element)}
        harmful_elements = {fe.get_overcome_element(stem_element), fe.get_overcome_element(branch_element)}
        story_logger.info(f"This makes {beneficial_elements} beneficial and {harmful_elements} harmful this round.")

        for zone in self.game_state.game_board.zones.values():
            zone.gold_reward = 0
            zone.gold_penalty = 0
            is_beneficial = zone.five_element in beneficial_elements
            is_harmful = zone.five_element in harmful_elements
            if zone.department == 'tian':
                if is_beneficial: zone.gold_reward += 5
                if is_harmful: zone.gold_reward = 0
            elif zone.department == 'di':
                if is_beneficial: zone.gold_penalty -= 3
                if is_harmful: zone.gold_penalty += 5
                zone.gold_penalty = max(0, zone.gold_penalty)

    def _choose_best_card_to_play(self, player: Player) -> Card | None:
        """A simple AI to choose a card to play based on the player's situation."""
        basic_cards = [c for c in player.hand if c.card_type == 'basic']
        if not basic_cards:
            return None

        # Heuristic: choose the card with the fewest strokes, as it's good for duels.
        best_card = min(basic_cards, key=lambda card: card.strokes)

        story_logger.info(f"  - {player.name} thinks about which card to play...")
        story_logger.info(f"  - They choose '{best_card.name}' because its low stroke count ({best_card.strokes}) is advantageous in duels (Lun Dao).")

        return best_card

    def _execute_placement_phase(self):
        self.game_state.set_phase("PLACEMENT")
        story_logger.info("\n--- Placement Phase ---")
        story_logger.info("Players decide which card to commit to this round's interpretation.")

        for player in self.active_players:
            card_to_play = self._choose_best_card_to_play(player)

            if card_to_play:
                player.play_card(card_to_play.card_id)
                story_logger.info(f"  - {player.name} places '{card_to_play.name}' face down.")
                logging.info(f"{player.name} 放置卡牌: {card_to_play.name} (面朝下)")
            else:
                story_logger.info(f"  - {player.name} has no basic cards to play this turn.")
                logging.info(f"{player.name} 没有基本卡牌可放置")

    def _choose_best_move(self, player: Player, valid_moves: List[str]) -> str:
        """A simple AI to choose the best move for a player."""
        move_scores = {}

        story_logger.info(f"  - {player.name} (at {player.position}) considers where to move.")

        for move in valid_moves:
            score = 0
            zone = self.game_state.game_board.get_zone(move)
            palace = self.game_state.game_board.get_palace_for_zone(move)
            gate_name = self.game_state.game_board.qimen_gates.get(palace)
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

            other_players = [p for p in self.active_players if p.position == move]
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

    def _execute_movement_phase(self):
        self.game_state.set_phase("MOVEMENT")
        story_logger.info("\n--- Movement Phase ---")
        story_logger.info("Players move across the board, triggering events.")

        for player in self.active_players:
            valid_moves = self.game_state.game_board.get_valid_moves(player.position)
            if not valid_moves:
                story_logger.info(f"  - {player.name} is at {player.position} and has no valid moves.")
                continue

            destination = self._choose_best_move(player, valid_moves)
            original_position = player.position
            player.position = destination
            story_logger.info(f"  - {player.name} moves from {original_position} to {destination}.")

            other_players_in_zone = [p for p in self.active_players if p.position == destination and p.player_id != player.player_id]
            if other_players_in_zone:
                defender = other_players_in_zone[0]
                story_logger.info(f"  - This triggers a 'Lun Dao' (duel) with {defender.name}!")
                self._trigger_lun_dao(player, defender)

        self._trigger_gate_effects()

    def _trigger_lun_dao(self, challenger: Player, defender: Player):
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
            self._check_player_elimination(loser)

        challenger.hand.remove(challenger_card)
        self.game_state.basic_discard_pile.append(challenger_card)
        defender.hand.remove(defender_card)
        self.game_state.basic_discard_pile.append(defender_card)
        story_logger.info("  - The cards used in the duel are discarded.")

    def _trigger_gate_effects(self):
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
        dun_type = self.game_state.dun_type
        ju_number = qm.get_ju_number_for_solar_term(self.game_state.solar_term_index, dun_type)
        gate_layout = qm.get_gate_layout_for_ju(ju_number, dun_type)
        if gate_layout:
            self.game_state.game_board.qimen_gates = gate_layout
            story_logger.info(f"The Qi Men gates have shifted for {dun_type} Dun Ju {ju_number}.")
        else:
            logging.error(f"Could not find gate layout for {dun_type} Dun Ju {ju_number}")

    def _execute_interpretation_phase(self):
        self.game_state.set_phase("INTERPRETATION")
        story_logger.info("\n--- Interpretation Phase ---")
        story_logger.info("Players reveal their cards and effects are triggered based on board order.")

        players_with_cards = [p for p in self.active_players if p.played_card]
        department_priority = {"tian": 0, "ren": 1, "di": 2, "zhong": 99}
        def get_interpretation_sort_key(player: Player):
            zone = self.game_state.game_board.get_zone(player.position)
            if not zone: return (99, 99)
            return (zone.luoshu_number, department_priority.get(zone.department, 99))

        players_with_cards.sort(key=get_interpretation_sort_key)

        for player in players_with_cards:
            card = player.played_card
            story_logger.info(f"  - {player.name} (at {player.position}) reveals '{card.name}'.")
            player_zone = self.game_state.game_board.get_zone(player.position)
            if not player_zone: continue

            variant_key = player_zone.department
            variant_effect = card.core_mechanism.get("variants", {}).get(variant_key, {}).get("effect")
            effect_to_queue = variant_effect if variant_effect else card.effect

            if effect_to_queue:
                self.effect_engine.queue_effect(effect_to_queue, player)
            else:
                logging.warning(f"Card {card.name} has no valid effect for department '{variant_key}'.")

        self.effect_engine.resolve_effects()
        for player in self.active_players: self._check_player_elimination(player)

    def _execute_resolution_phase(self):
        self.game_state.set_phase("RESOLUTION")
        story_logger.info("\n--- Resolution Phase ---")
        story_logger.info("Rewards and penalties from board positions are calculated.")

        for player in self.active_players:
            zone = self.game_state.game_board.get_zone(player.position)
            if not zone: continue

            if zone.department == 'tian':
                reward = zone.gold_reward
                if reward > 0:
                    player.change_resource("gold", reward)
                    self.game_state.game_fund -= reward
                    story_logger.info(f"  - {player.name} is in a Tian zone and gains {reward} gold.")
                else:
                    story_logger.info(f"  - {player.name} is in a stagnant Tian zone and gains no reward.")
            elif zone.department == 'di':
                penalty = zone.gold_penalty
                if penalty > 0:
                    paid_amount = min(player.gold, penalty)
                    player.change_resource("gold", -paid_amount)
                    self.game_state.game_fund += paid_amount
                    story_logger.info(f"  - {player.name} is in a Di zone and pays a penalty of {paid_amount} gold.")
            elif zone.department == 'zhong':
                penalty = math.ceil(player.gold * 0.10)
                player.change_resource("gold", -penalty)
                self.game_state.game_fund += penalty
                story_logger.info(f"  - {player.name} is in the Zhong Gong and pays a 10% tax of {penalty} gold.")

        for player in self.active_players: self._check_player_elimination(player)

    def _execute_upkeep_phase(self):
        self.game_state.set_phase("UPKEEP")
        story_logger.info("\n--- Upkeep Phase ---")
        
        for player in self.active_players:
            player.tick_statuses()
            if player.played_card:
                self.game_state.basic_discard_pile.append(player.played_card)
                player.played_card = None
        story_logger.info("  - Players discard used cards and status effects are updated.")
        
        self.game_state.advance_to_next_player()
        story_logger.info(f"  - The turn passes to the next player: {self.game_state.get_active_player().name}.")

    def _check_player_elimination(self, player: Player):
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