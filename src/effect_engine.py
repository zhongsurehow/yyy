import logging
import uuid
from typing import Dict, Any, List

# Forward-declare GameState to avoid circular import
if False:
    from .game_state import GameState
    from .player import Player


class EffectEngine:
    """Parses and executes card effect actions based on a priority queue."""

    def __init__(self, game_state: 'GameState'):
        self.game_state = game_state
        self.effect_queue = []
        self.action_handlers = {
            # Implemented
            "GAIN_RESOURCE": self._handle_gain_resource,
            "LOSE_RESOURCE": self._handle_lose_resource,
            "DEAL_DAMAGE": self._handle_deal_damage,
            "APPLY_STATUS": self._handle_apply_status,
            "REMOVE_STATUS": self._handle_remove_status,
            "MOVE": self._handle_move,
            "CHOICE": self._handle_choice,
            "MODIFY_RULE": self._handle_modify_rule,
            "INTERRUPT": self._handle_interrupt,
            "COPY_EFFECT": self._handle_copy_effect,
            "TRIGGER_EVENT": self._handle_trigger_event,
            "PAY_COST": self._handle_pay_cost,
            "DISCARD_CARD": self._handle_discard_card,
            "DRAW_CARD": self._handle_draw_card,
            "LOOKUP": self._handle_lookup,
            "CREATE_ENTITY": self._handle_create_entity,
            "TRANSFER_RESOURCE": self._handle_transfer_resource,

            # To be implemented
            "DESTROY_ENTITY": self._handle_destroy_entity,
            "EXECUTE_LATER": self._handle_execute_later,
            "PROPOSE_ALLIANCE": self._handle_propose_alliance,
            "RECOVER_CARD_FROM_DISCARD": self._handle_recover_card_from_discard,
            "SET_RESOURCE": self._handle_set_resource,
            "SKIP_PHASE": self._handle_skip_phase,
            "SWAP_HAND_CARDS": self._handle_swap_hand_cards,
            "SWAP_POSITION": self._handle_swap_position,
            "SWAP_RESOURCES": self._handle_swap_resources,
        }

    def queue_effect(self, effect: Dict[str, Any], source_player: 'Player', skip_costs=False):
        self.effect_queue.append({
            "effect": effect,
            "source_player": source_player,
            "skip_costs": skip_costs
        })
        logging.info(f"Queued effect from {source_player.name}")

    def resolve_effects(self):
        logging.info("== Resolving Effect Queue ==")
        self.effect_queue.sort(key=lambda item: self._get_effect_priority(item['effect']), reverse=True)

        for item in self.effect_queue:
            logging.info(f"Resolving effect for {item['source_player'].name} (Priority: {self._get_effect_priority(item['effect'])})")
            self._execute_resolved_effect(item['effect'], item['source_player'], item['skip_costs'])

        self.effect_queue = []
        logging.info("== Effect Queue Resolved ==")

    def _get_effect_priority(self, effect: Dict[str, Any]) -> int:
        actions = effect.get("actions", [])
        for action_data in actions:
            action_type = action_data.get("action")
            params = action_data.get("params", {})
            if action_type == "INTERRUPT" and params.get("interrupt_type") == "CANCEL": return 3
            if action_type == "APPLY_STATUS" and "CANNOT" in params.get("status_id", ""): return 3
            if action_type == "MODIFY_RULE": return 2
        return 1

    def _execute_resolved_effect(self, effect: Dict[str, Any], source_player: 'Player', skip_costs: bool):
        if "condition" in effect and not self._check_condition(effect["condition"], source_player):
            logging.warning(f"Condition not met for {source_player.name}. Effect aborted.")
            return

        if not skip_costs and "cost" in effect:
            if not self._pay_costs(effect["cost"], source_player):
                logging.warning(f"{source_player.name} could not pay costs. Effect aborted.")
                return

        actions = effect.get("actions", [])
        for action_data in actions:
            if self.game_state.interrupt_flags.get('next_action', False):
                logging.info("Action interrupted and cancelled!")
                self.game_state.interrupt_flags['next_action'] = False
                continue
            self.execute_action(action_data, source_player)

        self.game_state.last_resolved_effect = effect

    def execute_action(self, action_data: Dict[str, Any], source_player: 'Player'):
        action_type = action_data.get("action")
        params = action_data.get("params", {})
        handler = self.action_handlers.get(action_type, self._handle_unimplemented)
        logging.debug(f"Executing Action: {action_type} for {source_player.name}")
        if handler == self._handle_unimplemented:
            handler(params, source_player, action_type=action_type)
        else:
            handler(params, source_player)

    def _get_targets(self, target_str: str, source_player: 'Player') -> List['Player']:
        if target_str == "SELF": return [source_player]

        opponents = [p for p in self.game_state.players if p.player_id != source_player.player_id and not p.is_eliminated]
        allies = [p for p in self.game_state.players if p.player_id in source_player.allies and not p.is_eliminated]

        if target_str == "OPPONENT_ALL": return opponents
        if target_str == "ALL_PLAYERS": return self.game_state.players
        if target_str == "ALLY_FORMAL_ALL": return allies

        if target_str in ("OPPONENT_CHOICE_SINGLE", "PLAYER_CHOICE_ANY", "PLAYER_CHOICE_ANY_NON_ALLY"):
            # Simplified for simulation: pick first opponent/player
            if opponents: return [opponents[0]]
            return []

        if target_str == "ALLY_FORMAL_SINGLE" or target_str == "ALLY_FORMAL_SINGLE_CHOICE":
            if allies: return [allies[0]] # Simplified: pick first ally
            return []

        if target_str == "OTHER_PLAYERS_IN_SAME_ZONE":
            if source_player.position is None: return []
            return [p for p in self.game_state.players if p != source_player and p.position == source_player.position]

        logging.warning(f"Target type '{target_str}' not fully implemented. Defaulting to SELF.")
        return [source_player]

    def _resolve_value(self, value: Any, source_player: 'Player') -> int:
        if isinstance(value, int): return value
        if isinstance(value, dict):
            op = value.get("op")
            if op == "COUNT":
                target_str = value.get("target")
                return len(self._get_targets(target_str, source_player))
            else:
                logging.warning(f"Dynamic value operator '{op}' not implemented. Defaulting to 0.")
                return 0
        return 0

    # --- Action Handlers ---

    def _handle_gain_resource(self, params: Dict[str, Any], source_player: 'Player'):
        for target in self._get_targets(params.get("target", "SELF"), source_player):
            target.change_resource(params.get("resource"), self._resolve_value(params.get("value"), source_player))

    def _handle_lose_resource(self, params: Dict[str, Any], source_player: 'Player'):
        for target in self._get_targets(params.get("target", "SELF"), source_player):
            target.change_resource(params.get("resource"), -self._resolve_value(params.get("value"), source_player))

    def _handle_set_resource(self, params: Dict[str, Any], source_player: 'Player'):
        for target in self._get_targets(params.get("target", "SELF"), source_player):
            setattr(target, params.get("resource").lower(), self._resolve_value(params.get("value"), source_player))
            logging.info(f"Set {target.name}'s {params.get('resource')} to {params.get('value')}.")

    def _handle_deal_damage(self, params: Dict[str, Any], source_player: 'Player'):
        for target in self._get_targets(params.get("target", "OPPONENT_CHOICE_SINGLE"), source_player):
            target.change_resource("health", -self._resolve_value(params.get("value"), source_player))

    def _handle_apply_status(self, params: Dict[str, Any], source_player: 'Player'):
        for target in self._get_targets(params.get("target"), source_player):
            target.add_status(params.copy())

    def _handle_remove_status(self, params: Dict[str, Any], source_player: 'Player'):
        for target in self._get_targets(params.get("target"), source_player):
            target.remove_status(params.get("status_id"))

    def _handle_move(self, params: Dict[str, Any], source_player: 'Player'):
        logging.info(f"Movement action triggered for {source_player.name}.")
        # Actual move logic is handled in the game loop for now.

    def _handle_choice(self, params: Dict[str, Any], source_player: 'Player'):
        options = params.get("options", [])
        if options:
            logging.info("Player has a choice. For prototype, auto-selecting first valid option.")
            first_option = options[0]
            if "effect" in first_option:
                self._execute_resolved_effect(first_option["effect"], source_player, skip_costs=False)

    def _handle_modify_rule(self, params: Dict[str, Any], source_player: 'Player'):
        self.game_state.active_rules[params.get("rule_id")] = params
        logging.info(f"Rule Modified: '{params.get('rule_id')}'")

    def _handle_interrupt(self, params: Dict[str, Any], source_player: 'Player'):
        self.game_state.interrupt_flags['next_action'] = (params.get("interrupt_type", "CANCEL") == "CANCEL")

    def _handle_copy_effect(self, params: Dict[str, Any], source_player: 'Player'):
        if not self.game_state.last_resolved_effect:
            logging.warning("COPY_EFFECT failed: No previous effect.")
            return
        for target in self._get_targets(params.get("target", "SELF"), source_player):
            self._execute_resolved_effect(self.game_state.last_resolved_effect, target, skip_costs=True)

    def _handle_trigger_event(self, params: Dict[str, Any], source_player: 'Player'):
        logging.warning(f"Event '{params.get('event_id')}' triggered. (Logic to be implemented)")

    def _handle_pay_cost(self, params: Dict[str, Any], source_player: 'Player'):
        resource = params.get("resource")
        value = self._resolve_value(params.get("value"), source_player)
        if not source_player.can_afford(resource, value):
            raise ValueError(f"Cannot afford cost: {value} {resource}")
        source_player.change_resource(resource, -value)

    def _handle_discard_card(self, params: Dict[str, Any], source_player: 'Player'):
        # Simplified: discard a random card
        if source_player.hand:
            card_to_discard = source_player.hand.pop()
            self.game_state.basic_discard_pile.append(card_to_discard)
            logging.info(f"{source_player.name} discarded {card_to_discard.name}.")

    def _handle_draw_card(self, params: Dict[str, Any], source_player: 'Player'):
        # Simplified: draw from basic deck
        if self.game_state.basic_deck:
            card = self.game_state.basic_deck.pop()
            source_player.add_card_to_hand(card)
            logging.info(f"{source_player.name} drew {card.name}.")

    def _handle_lookup(self, params: Dict[str, Any], source_player: 'Player'):
        logging.warning(f"LOOKUP action is not fully implemented.")

    def _handle_create_entity(self, params: Dict[str, Any], source_player: 'Player'):
        entity_id = str(uuid.uuid4())
        self.game_state.entities[entity_id] = params
        logging.info(f"{source_player.name} created entity {params.get('entity_type')} at {params.get('position')}.")

    def _handle_destroy_entity(self, params: Dict[str, Any], source_player: 'Player'):
        # Simplified: just log it
        logging.info(f"{source_player.name} destroyed an entity.")

    def _handle_transfer_resource(self, params: Dict[str, Any], source_player: 'Player'):
        targets = self._get_targets(params.get("to"), source_player)
        resource = params.get("resource")
        value = self._resolve_value(params.get("value"), source_player)
        for target in targets:
            source_player.change_resource(resource, -value)
            target.change_resource(resource, value)
            logging.info(f"{source_player.name} transferred {value} {resource} to {target.name}.")

    def _handle_execute_later(self, params: Dict[str, Any], source_player: 'Player'):
        self.game_state.delayed_effects.append({
            "effect": params.get("effect"),
            "source_player": source_player,
            "delay": params.get("delay", "NEXT_TURN_START"),
            "turn": self.game_state.current_turn
        })
        logging.info(f"Effect scheduled to execute later for {source_player.name}.")

    def _handle_propose_alliance(self, params: Dict[str, Any], source_player: 'Player'):
        targets = self._get_targets(params.get("target"), source_player)
        # Simplified: Alliance is automatically accepted
        for target in targets:
            if source_player.player_id not in target.allies:
                target.allies.append(source_player.player_id)
            if target.player_id not in source_player.allies:
                source_player.allies.append(target.player_id)
            logging.info(f"{source_player.name} and {target.name} are now allies.")

            if "on_accept_effect" in params:
                 self._execute_resolved_effect(params["on_accept_effect"], source_player, skip_costs=False)

    def _handle_recover_card_from_discard(self, params: Dict[str, Any], source_player: 'Player'):
        if self.game_state.basic_discard_pile:
            card = self.game_state.basic_discard_pile.pop()
            source_player.add_card_to_hand(card)
            logging.info(f"{source_player.name} recovered {card.name} from the discard pile.")

    def _handle_skip_phase(self, params: Dict[str, Any], source_player: 'Player'):
        self.game_state.skipped_phases.add(params.get("phase"))
        logging.info(f"{source_player.name} will skip the {params.get('phase')} phase.")

    def _handle_swap_hand_cards(self, params: Dict[str, Any], source_player: 'Player'):
        # Simplified: swap entire hands
        targets = self._get_targets(params.get("other_player"), source_player)
        if not targets: return
        target = targets[0]
        source_player.hand, target.hand = target.hand, source_player.hand
        logging.info(f"{source_player.name} and {target.name} swapped their hands.")

    def _handle_swap_position(self, params: Dict[str, Any], source_player: 'Player'):
        target_a_list = self._get_targets(params.get("target_a"), source_player)
        target_b_list = self._get_targets(params.get("target_b"), source_player)
        if not target_a_list or not target_b_list: return
        target_a, target_b = target_a_list[0], target_b_list[0]
        target_a.position, target_b.position = target_b.position, target_a.position
        logging.info(f"{target_a.name} and {target_b.name} swapped positions.")

    def _handle_swap_resources(self, params: Dict[str, Any], source_player: 'Player'):
        target_a_list = self._get_targets(params.get("target_a"), source_player)
        target_b_list = self._get_targets(params.get("target_b"), source_player)
        if not target_a_list or not target_b_list: return
        target_a, target_b = target_a_list[0], target_b_list[0]
        resource = params.get("resource").lower()

        res_a = getattr(target_a, resource)
        res_b = getattr(target_b, resource)
        setattr(target_a, resource, res_b)
        setattr(target_b, resource, res_a)
        logging.info(f"{target_a.name} and {target_b.name} swapped their {resource}.")

    def _handle_unimplemented(self, params: Dict[str, Any], source_player: 'Player', action_type: str = "Unknown"):
        logging.warning(f"Action '{action_type}' is not yet implemented.")

    def _check_condition(self, condition: Dict[str, Any], source_player: 'Player') -> bool:
        logging.warning(f"Condition check is a stub. Defaulting to TRUE.")
        return True

    def _pay_costs(self, costs: List[Dict[str, Any]], source_player: 'Player') -> bool:
        for cost_data in costs:
            if cost_data.get("action") == "DISCARD_CARD":
                if not source_player.hand: return False
            else:
                resource = cost_data.get("resource")
                value = self._resolve_value(cost_data.get("value"), source_player)
                if not source_player.can_afford(resource, value):
                    return False

        for cost_data in costs:
            if cost_data.get("action") == "DISCARD_CARD":
                self._handle_discard_card({}, source_player)
            else:
                source_player.change_resource(cost_data.get("resource"), -self._resolve_value(cost_data.get("value"), source_player))
        return True