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

        # Set up the game fund based on player count
        self.game_state.game_fund = len(self.game_state.players) * 100
        logging.info(f"Game fund initialized to: {self.game_state.game_fund}")

        # Set initial Qi Men gate layout
        self._update_qimen_gates()

        # Manually set player positions for specific testing
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

        logging.info("Game setup complete.")

    def run_game(self, num_rounds: int = 1):
        """Runs the main game loop for a specified number of rounds."""
        logging.info(f"--- Starting Game Run ({num_rounds} round(s)) ---")

        for i in range(1, num_rounds + 1):
            self.run_round(i)

        logging.info("--- Game Run Finished ---")
        logging.info("Final Player States:")
        for player in self.game_state.players:
            logging.info(f"  - {player}")

    def run_round(self, round_number: int):
        """Executes all phases for a single round of the game."""
        if len(self.active_players) <= 1:
            logging.info("Not enough active players to continue. Ending game.")
            return

        self.game_state.current_turn = round_number
        logging.info(f"***** Round {self.game_state.current_turn} *****")

        self._execute_time_phase()
        self._execute_placement_phase()
        self._execute_movement_phase()
        self._execute_interpretation_phase()
        self._execute_resolution_phase()
        self._execute_upkeep_phase()

    def _execute_time_phase(self):
        self.game_state.set_phase("TIME")
        logging.info("--- Phase: TIME ---")
        logging.info(f"当前局数: 阳遁第{self.game_state.ju_number}局")

        # Update Qi Men gates based on the current Ju number
        self._update_qimen_gates()

        # 1. Discard previous Gan-Zhi cards
        if self.game_state.current_celestial_stem:
            logging.info(f"弃置天干牌: {self.game_state.current_celestial_stem.name}")
            self.game_state.celestial_stem_discard_pile.append(self.game_state.current_celestial_stem)
        if self.game_state.current_terrestrial_branch:
            logging.info(f"弃置地支牌: {self.game_state.current_terrestrial_branch.name}")
            self.game_state.terrestrial_branch_discard_pile.append(self.game_state.current_terrestrial_branch)

        # 2. Draw new stem and branch cards, reshuffling if necessary
        self._reshuffle_if_needed('celestial_stem')
        self._reshuffle_if_needed('terrestrial_branch')

        if not self.game_state.celestial_stem_deck or not self.game_state.terrestrial_branch_deck:
            logging.error("Celestial Stem or Terrestrial Branch deck (and discard) is empty. Cannot proceed.")
            return # This is a critical failure, game cannot continue

        self.game_state.current_celestial_stem = self.game_state.celestial_stem_deck.pop()
        self.game_state.current_terrestrial_branch = self.game_state.terrestrial_branch_deck.pop()
        logging.info(f"新干支牌: {self.game_state.current_celestial_stem.name}, {self.game_state.current_terrestrial_branch.name}")

        # 3. Determine beneficial and harmful elements
        stem_element = fe.get_element_for_stem(self.game_state.current_celestial_stem.card_id.split('_')[-1])
        branch_element = fe.get_element_for_branch(self.game_state.current_terrestrial_branch.card_id.split('_')[-1])

        beneficial_elements = {fe.get_generated_element(stem_element), fe.get_generated_element(branch_element)}
        harmful_elements = {fe.get_overcome_element(stem_element), fe.get_overcome_element(branch_element)}
        logging.info(f"有益元素: {beneficial_elements}, 有害元素: {harmful_elements}")

        # 4. Update all zones on the board
        zone_updates = []
        for zone in self.game_state.game_board.zones.values():
            # Reset previous values
            zone.gold_reward = 0
            zone.gold_penalty = 0

            is_beneficial = zone.five_element in beneficial_elements
            is_harmful = zone.five_element in harmful_elements

            if zone.department == 'tian':
                if is_beneficial:
                    zone.gold_reward += 5
                    zone_updates.append(f"{zone.zone_id}(天部): +5金币")
                if is_harmful: # Stagnation rule overrides reward
                    zone.gold_reward = 0
                    zone_updates.append(f"{zone.zone_id}(天部): 停滞无奖励")

            elif zone.department == 'di':
                if is_beneficial:
                    zone.gold_penalty -= 3
                    zone_updates.append(f"{zone.zone_id}(地部): 惩罚-3")
                if is_harmful:
                    zone.gold_penalty += 5
                    zone_updates.append(f"{zone.zone_id}(地部): 惩罚+5")
                zone.gold_penalty = max(0, zone.gold_penalty) # Cannot be negative

        if zone_updates:
            logging.info("区域更新: " + ", ".join(zone_updates))

    def _execute_placement_phase(self):
        self.game_state.set_phase("PLACEMENT")
        logging.info("--- Phase: PLACEMENT ---")
        for player in self.active_players:
            # Players randomly choose a basic card from their hand to play.
            basic_cards_in_hand = [c for c in player.hand if c.card_type == 'basic']
            if basic_cards_in_hand:
                card_to_play = random.choice(basic_cards_in_hand)
                player.play_card(card_to_play.card_id)
                logging.info(f"{player.name} 放置卡牌: {card_to_play.name} (面朝下)")
                logging.info(f"{player.name} 手牌数量: {len(player.hand)}")
            else:
                logging.info(f"{player.name} 没有基本卡牌可放置")

    def _execute_movement_phase(self):
        self.game_state.set_phase("MOVEMENT")
        logging.info("--- Phase: MOVEMENT ---")

        # Simplified: players move one by one in the current player order
        for player in self.active_players:
            # In a full game, we'd check if the player can move (e.g., not stunned)
            valid_moves = self.game_state.game_board.get_valid_moves(player.position)
            if not valid_moves:
                logging.info(f"{player.name} 在 {player.position} 没有可移动的位置")
                continue

            # Players randomly choose a valid move.
            destination = random.choice(valid_moves)
            original_position = player.position
            player.position = destination
            logging.info(f"{player.name} 从 {original_position} 移动到 {destination}")

            # Check for "Lun Dao"
            other_players_in_zone = [
                p for p in self.active_players
                if p.position == destination and p.player_id != player.player_id
            ]

            if other_players_in_zone:
                defender = other_players_in_zone[0] # Simplified: challenge the first player found
                logging.info(f"触发论道: {player.name} vs {defender.name}")
                self._trigger_lun_dao(player, defender)
            else:
                logging.info(f"{player.name} 移动到空区域")

        # After all movements are complete, trigger Qi Men gate effects
        self._trigger_gate_effects()

    def _trigger_lun_dao(self, challenger: Player, defender: Player):
        logging.info(f"--- 论道事件触发: {challenger.name} vs {defender.name} ---")

        # Players randomly choose a basic card from their hand for the duel.
        challenger_cards = [c for c in challenger.hand if c.card_type == 'basic']
        defender_cards = [c for c in defender.hand if c.card_type == 'basic']

        if not challenger_cards or not defender_cards:
            logging.warning("论道无法进行，一方或双方缺少基本卡牌")
            return

        challenger_card = random.choice(challenger_cards)
        defender_card = random.choice(defender_cards)

        logging.info(f"{challenger.name} 展示: {challenger_card.name} ({challenger_card.strokes}笔画)")
        logging.info(f"{defender.name} 展示: {defender_card.name} ({defender_card.strokes}笔画)")

        winner, loser = (None, None)
        if challenger_card.strokes < defender_card.strokes:
            winner, loser = challenger, defender
            logging.info(f"{challenger.name} 笔画数更少，获胜！")
        elif defender_card.strokes < challenger_card.strokes:
            winner, loser = defender, challenger
            logging.info(f"{defender.name} 笔画数更少，获胜！")
        else:
            logging.info("笔画数相同，平局！")

        if winner:
            amount = min(loser.gold, 5) # Cannot take more than the loser has
            loser.change_resource("gold", -amount)
            winner.change_resource("gold", amount)
            logging.info(f"{winner.name} 从 {loser.name} 处获得 {amount}金币")
            logging.info(f"{winner.name} 金币: {winner.gold}, {loser.name} 金币: {loser.gold}")
            self._check_player_elimination(loser)
        else:
            logging.info("论道平局，双方相安无事")

        # Discard the used cards
        challenger.hand.remove(challenger_card)
        self.game_state.basic_discard_pile.append(challenger_card)
        defender.hand.remove(defender_card)
        self.game_state.basic_discard_pile.append(defender_card)
        logging.info("论道使用的卡牌已弃置")

    def _trigger_gate_effects(self):
        """Triggers the Qi Men gate effects for all players based on their current position."""
        logging.info("--- 触发奇门八门效果 ---")
        gate_effects_triggered = []
        
        for player in self.active_players:
            palace = self.game_state.game_board.get_palace_for_zone(player.position)
            if not palace:
                continue

            gate_name = self.game_state.game_board.qimen_gates.get(palace)
            if gate_name:
                gate_info = qm.GATE_EFFECTS.get(gate_name, {})
                gate_display_name = gate_info.get("name", gate_name)
                logging.info(f"{player.name} 在 {palace.upper()}宫，触发: {gate_display_name}")
                gate_effects_triggered.append(f"{player.name}: {gate_display_name}")
                
                gate_effect = qm.get_effect_for_gate(gate_name)
                if gate_effect:
                    self.effect_engine.queue_effect(gate_effect, player)

        if gate_effects_triggered:
            logging.info("奇门效果触发: " + ", ".join(gate_effects_triggered))
        else:
            logging.info("本回合无奇门效果触发")

        # Resolve any queued gate effects
        self.effect_engine.resolve_effects()

        # After gate effects, check for elimination
        for player in self.active_players:
            self._check_player_elimination(player)

    def _update_qimen_gates(self):
        """Updates the gate layout on the board based on the current Ju number."""
        ju_number = self.game_state.ju_number
        gate_layout = qm.get_gate_layout_for_ju(ju_number)
        if gate_layout:
            self.game_state.game_board.qimen_gates = gate_layout
            logging.info(f"Qi Men gates updated for Ju {ju_number}: {gate_layout}")
        else:
            logging.error(f"Could not find gate layout for Ju {ju_number}")

    def _execute_interpretation_phase(self):
        self.game_state.set_phase("INTERPRETATION")
        logging.info("--- Phase: INTERPRETATION ---")

        players_with_cards = [p for p in self.active_players if p.played_card]

        # Define department priority for sorting
        department_priority = {"tian": 0, "ren": 1, "di": 2, "zhong": 99}

        def get_interpretation_sort_key(player: Player):
            zone = self.game_state.game_board.get_zone(player.position)
            if not zone:
                # Players in invalid positions resolve last
                return (99, 99)
            luoshu = zone.luoshu_number
            dept_prio = department_priority.get(zone.department, 99)
            return (luoshu, dept_prio)

        # Sort players according to the game rules
        players_with_cards.sort(key=get_interpretation_sort_key)

        logging.info("Players reveal and queue their card effects according to board position.")
        for player in players_with_cards:
            card = player.played_card
            logging.info(f"{player.name} (at {player.position}) reveals {card.name}!")

            player_zone = self.game_state.game_board.get_zone(player.position)
            # This check is somewhat redundant due to the sort key, but safe to keep
            if not player_zone:
                logging.warning(f"Player {player.name} is at an invalid position {player.position}, skipping interpretation.")
                continue

            variant_key = player_zone.department
            variant_effect = card.core_mechanism.get("variants", {}).get(variant_key, {}).get("effect")
            effect_to_queue = variant_effect if variant_effect else card.effect

            if effect_to_queue:
                self.effect_engine.queue_effect(effect_to_queue, player)
            else:
                logging.warning(f"Card {card.name} has no valid effect for department '{variant_key}' or a default effect.")

        # After all effects are queued, resolve them based on priority
        self.effect_engine.resolve_effects()

        # After effects resolve, check for elimination
        for player in self.active_players:
            self._check_player_elimination(player)

    def _execute_resolution_phase(self):
        self.game_state.set_phase("RESOLUTION")
        logging.info("--- Phase: RESOLUTION ---")
        logging.info("计算天部奖励和地部惩罚...")

        for player in self.active_players:
            zone = self.game_state.game_board.get_zone(player.position)
            if not zone:
                continue

            # Tian Bu Reward
            if zone.department == 'tian':
                reward = zone.gold_reward
                if reward > 0:
                    player.change_resource("gold", reward)
                    self.game_state.game_fund -= reward
                    logging.info(f"{player.name} 在天部获得 {reward}金币. 基金剩余: {self.game_state.game_fund}")
                else:
                    logging.info(f"{player.name} 在天部无奖励")

            # Di Bu Penalty
            elif zone.department == 'di':
                penalty = zone.gold_penalty
                if penalty > 0:
                    paid_amount = min(player.gold, penalty)
                    player.change_resource("gold", -paid_amount)
                    self.game_state.game_fund += paid_amount
                    logging.info(f"{player.name} 在地部支付 {paid_amount}金币惩罚. 基金剩余: {self.game_state.game_fund}")
                else:
                    logging.info(f"{player.name} 在地部无惩罚")

            # Zhong Gong Penalty
            elif zone.department == 'zhong':
                penalty = math.ceil(player.gold * 0.10)
                player.change_resource("gold", -penalty)
                self.game_state.game_fund += penalty
                logging.info(f"{player.name} 在中宫支付 {penalty}金币(10%)惩罚. 基金剩余: {self.game_state.game_fund}")

        # After all transactions, check for elimination
        for player in self.active_players:
            self._check_player_elimination(player)

    def _execute_upkeep_phase(self):
        self.game_state.set_phase("UPKEEP")
        logging.info("--- Phase: UPKEEP ---")
        logging.info("处理维护阶段...")
        
        # Log player status before upkeep
        for player in self.active_players:
            logging.info(f"{player.name} 状态: 生命{player.health}, 金币{player.gold}, 手牌{len(player.hand)}")
        
        for player in self.active_players:
            player.tick_statuses()
            if player.played_card:
                # For now, assume all played cards are basic cards.
                self.game_state.basic_discard_pile.append(player.played_card)
                player.played_card = None
        logging.info("玩家弃置已使用的卡牌")
        
        # Advance to next player after upkeep phase
        self.game_state.advance_to_next_player()
        logging.info(f"推进到下一位玩家: {self.game_state.get_active_player().name}")
        logging.info(f"当前局数: 阳遁第{self.game_state.ju_number}局, 回合: {self.game_state.current_turn}")

    def _check_player_elimination(self, player: Player):
        """Checks if a player should be eliminated and updates their status."""
        if player.is_eliminated:
            return # Already eliminated

        # Elimination condition: Health is 0 or less.
        # Rule 13.1 also mentions gold, but we'll start with health.
        if player.health <= 0:
            player.is_eliminated = True
            logging.warning(f"PLAYER ELIMINATED: {player.name} has been eliminated (Health: {player.health}).")
            # In a full game, we might trigger "on elimination" effects here.

    def _get_deck_and_discard(self, deck_type: str) -> (List[Card], List[Card]):
        gs = self.game_state
        if deck_type == 'basic':
            return gs.basic_deck, gs.basic_discard_pile
        elif deck_type == 'function':
            return gs.function_deck, gs.function_discard_pile
        elif deck_type == 'celestial_stem':
            return gs.celestial_stem_deck, gs.celestial_stem_discard_pile
        elif deck_type == 'terrestrial_branch':
            return gs.terrestrial_branch_deck, gs.terrestrial_branch_discard_pile
        logging.warning(f"Unknown deck type requested: {deck_type}")
        return None, None

    def _reshuffle_if_needed(self, deck_type: str):
        deck, discard_pile = self._get_deck_and_discard(deck_type)
        if deck is None:
            return

        if not deck:
            if len(discard_pile) > 0:
                logging.info(f"Deck '{deck_type}' is empty. Reshuffling discard pile.")
                deck.extend(discard_pile)
                random.shuffle(deck)
                discard_pile.clear()
            else:
                logging.warning(f"Deck '{deck_type}' and its discard pile are both empty. Cannot draw.")