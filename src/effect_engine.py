import logging
from typing import Dict, Any, List

# Forward-declare GameState to avoid circular import
if False:
    from game_state import GameState
    from player import Player

class EffectEngine:
    """Parses and executes card effect actions based on a priority queue."""

    def __init__(self, game_state: 'GameState'):
        self.game_state = game_state
        self.effect_queue = []
        self.action_handlers = {
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
        }

    def queue_effect(self, effect: Dict[str, Any], source_player: 'Player', skip_costs=False):
        """Adds an effect to the queue to be resolved."""
        self.effect_queue.append({
            "effect": effect,
            "source_player": source_player,
            "skip_costs": skip_costs
        })
        logging.info(f"Queued effect from {source_player.name}")

    def resolve_effects(self):
        """Sorts and executes all effects in the queue according to priority."""
        logging.info("== Resolving Effect Queue ==")
        # Sort the queue based on priority. Higher numbers are higher priority.
        self.effect_queue.sort(key=lambda item: self._get_effect_priority(item['effect']), reverse=True)

        for item in self.effect_queue:
            logging.info(f"Resolving effect for {item['source_player'].name} (Priority: {self._get_effect_priority(item['effect'])})")
            self._execute_resolved_effect(item['effect'], item['source_player'], item['skip_costs'])

        # Clear the queue after resolution
        self.effect_queue = []
        logging.info("== Effect Queue Resolved ==")

    def _get_effect_priority(self, effect: Dict[str, Any]) -> int:
        """
        Determines the priority of an effect based on the simplified 3-tier model.
        Tier 1 (Cannot-Layer): 3
        Tier 2 (Rules-Change-Layer): 2
        Tier 3 (Standard-Layer): 1
        """
        actions = effect.get("actions", [])
        for action_data in actions:
            action_type = action_data.get("action")
            params = action_data.get("params", {})
            # Tier 1: "Cannot" effects
            if action_type == "INTERRUPT" and params.get("interrupt_type") == "CANCEL":
                return 3
            if action_type == "APPLY_STATUS" and "CANNOT" in params.get("status_id", ""):
                return 3

            # Tier 2: Other rule-changing effects
            if action_type == "MODIFY_RULE":
                return 2

        # Tier 3: Standard effects
        return 1

    def _execute_resolved_effect(self, effect: Dict[str, Any], source_player: 'Player', skip_costs: bool):
        """
        (Internal) Executes a single, resolved effect block.
        This contains the original logic of checking costs and conditions.
        """
        # 1. Check Conditions
        if "condition" in effect and not self._check_condition(effect["condition"], source_player):
            logging.warning(f"Condition not met for {source_player.name}. Effect aborted.")
            return

        # 2. Pay Costs
        if not skip_costs and "cost" in effect:
            if not self._pay_costs(effect["cost"], source_player):
                logging.warning(f"{source_player.name} could not pay costs. Effect aborted.")
                return

        # 3. Execute Actions
        actions = effect.get("actions", [])
        for action_data in actions:
            # Check for interrupts before each action
            if self.game_state.interrupt_flags.get('next_action', False):
                logging.info("Action interrupted and cancelled!")
                self.game_state.interrupt_flags['next_action'] = False # Consume the flag
                continue # Skip this action
            self.execute_action(action_data, source_player)

        # 4. Store for future reference (e.g., COPY_EFFECT)
        self.game_state.last_resolved_effect = effect

    def execute_action(self, action_data: Dict[str, Any], source_player: 'Player'):
        """Executes a single action from an effect block using the handler map."""
        action_type = action_data.get("action")
        params = action_data.get("params", {})

        handler = self.action_handlers.get(action_type, self._handle_unimplemented)

        logging.debug(f"Executing Action: {action_type} for {source_player.name}")
        if handler == self._handle_unimplemented:
            handler(params, source_player, action_type=action_type)
        else:
            handler(params, source_player)

    def _get_targets(self, target_str: str, source_player: 'Player') -> List['Player']:
        """Resolves a target string into a list of Player objects."""
        if target_str == "SELF":
            return [source_player]

        opponents = [p for p in self.game_state.players if p != source_player]

        if target_str == "OPPONENT_ALL":
            return opponents

        if target_str == "OPPONENT_CHOICE_SINGLE":
            # In a real game, this would prompt the source_player for a choice.
            # For now, we'll default to the first opponent as a placeholder.
            logging.info("OPPONENT_CHOICE_SINGLE is not interactive. Defaulting to first opponent.")
            return [opponents[0]] if opponents else []

        if target_str == "ALL_PLAYERS":
            return self.game_state.players

        if target_str == "OTHER_PLAYERS_IN_SAME_ZONE":
            if source_player.position is None:
                return []
            return [
                p for p in self.game_state.players
                if p != source_player and p.position == source_player.position
            ]

        # --- Event-based targets (placeholders for now) ---
        if target_str == "EVENT_SOURCE_PLAYER":
            logging.warning(f"Target type '{target_str}' requires event context, which is not yet implemented. Defaulting to SELF.")
            return [source_player]

        logging.warning(f"Target type '{target_str}' not fully implemented. Defaulting to SELF.")
        return [source_player]

    def _resolve_value(self, value: Any, source_player: 'Player') -> int:
        """Resolves a value that can be an integer or a dynamic dictionary."""
        if isinstance(value, int):
            return value
        if isinstance(value, dict):
            op = value.get("op")
            if op == "COUNT":
                target_str = value.get("target")
                return len(self._get_targets(target_str, source_player))
            # Other ops like 'SUM', 'PLAYER_RESOURCE' would go here
            else:
                logging.warning(f"Dynamic value operator '{op}' not implemented. Defaulting to 0.")
                return 0
        return 0 # Default for unexpected types

    # --- Resource Handlers ---
    def _handle_gain_resource(self, params: Dict[str, Any], source_player: 'Player'):
        targets = self._get_targets(params.get("target", "SELF"), source_player)
        value = self._resolve_value(params.get("value"), source_player)
        resource = params.get("resource")

        for target in targets:
            target.change_resource(resource, value)
            logging.debug(f"Target: {target.name}, Resource: {resource}, Value: +{value}")

    def _handle_lose_resource(self, params: Dict[str, Any], source_player: 'Player'):
        targets = self._get_targets(params.get("target", "SELF"), source_player)
        value = self._resolve_value(params.get("value"), source_player)
        resource = params.get("resource")

        for target in targets:
            target.change_resource(resource, -value)
            logging.debug(f"Target: {target.name}, Resource: {resource}, Value: -{value}")

    def _handle_deal_damage(self, params: Dict[str, Any], source_player: 'Player'):
        targets = self._get_targets(params.get("target", "OPPONENT_CHOICE_SINGLE"), source_player)
        value = self._resolve_value(params.get("value"), source_player)

        for target in targets:
            target.change_resource("health", -value)
            logging.info(f"Target: {target.name} takes {value} damage!")

    # --- Status Handlers ---
    def _handle_apply_status(self, params: Dict[str, Any], source_player: 'Player'):
        targets = self._get_targets(params.get("target"), source_player)
        status_to_apply = {
            "status_id": params.get("status_id"),
            "duration": params.get("duration", 1),
            "value": params.get("value"),
            "is_permanent": params.get("is_permanent", False)
        }
        for target in targets:
            target.add_status(status_to_apply.copy())

    def _handle_remove_status(self, params: Dict[str, Any], source_player: 'Player'):
        targets = self._get_targets(params.get("target"), source_player)
        status_id_to_remove = params.get("status_id")
        for target in targets:
            target.remove_status(status_id_to_remove)

    # --- Other Handlers ---
    def _handle_move(self, params: Dict[str, Any], source_player: 'Player'):
        logging.info(f"Movement action triggered. (Logic to be implemented)")
        source_player.has_moved = True

    def _handle_choice(self, params: Dict[str, Any], source_player: 'Player'):
        options = params.get("options", [])
        if options:
            logging.info("Player has a choice. For prototype, auto-selecting first valid option.")
            first_option = options[0]
            if "effect" in first_option:
                self._execute_resolved_effect(first_option["effect"], source_player, skip_costs=True)
        else:
            logging.warning("CHOICE action has no options.")

    def _handle_modify_rule(self, params: Dict[str, Any], source_player: 'Player'):
        rule_id = params.get("rule_id")
        mutation = params.get("mutation")
        duration = params.get("duration", 1)  # Default duration of 1 turn

        self.game_state.active_rules[rule_id] = {
            "mutation": mutation,
            "duration": duration,
            "source_player_id": source_player.player_id
        }
        logging.info(f"Rule Modified: '{rule_id}' set to {mutation} for {duration} turn(s).")

    def _handle_interrupt(self, params: Dict[str, Any], source_player: 'Player'):
        interrupt_type = params.get("interrupt_type", "CANCEL")
        # In a full engine, this would hook into a deeper event queue.
        # For now, we set a simple flag that the game loop should check.
        self.game_state.interrupt_flags['next_action'] = (interrupt_type == "CANCEL")
        logging.info(f"INTERRUPT action: Set 'next_action' interrupt flag to {self.game_state.interrupt_flags['next_action']}.")

    def _handle_copy_effect(self, params: Dict[str, Any], source_player: 'Player'):
        # This is a simplified implementation. A full version would need to handle
        # complex targeting and modifications as per the schema.
        last_effect = self.game_state.last_resolved_effect
        if not last_effect:
            logging.warning("COPY_EFFECT failed: No previous effect to copy.")
            return

        target_str = params.get("target", "SELF")
        targets = self._get_targets(target_str, source_player)

        logging.info(f"Copying last effect for {', '.join([p.name for p in targets])}")
        for target_player in targets:
            # Execute the copied effect, but skip costs.
            # A full implementation would need to re-evaluate context ('SELF' should mean the copier).
            self._execute_resolved_effect(last_effect, target_player, skip_costs=True)

    def _handle_trigger_event(self, params: Dict[str, Any], source_player: 'Player'):
        logging.info(f"Event '{params.get('event_id')}' triggered. (Logic to be implemented)")

    def _handle_pay_cost(self, params: Dict[str, Any], source_player: 'Player'):
        resource = params.get("resource")
        value = self._resolve_value(params.get("value"), source_player)

        if not source_player.can_afford(resource, value):
            raise ValueError(f"{source_player.name} cannot afford cost: {value} {resource}")

        source_player.change_resource(resource, -value)
        logging.debug(f"Cost Paid: {source_player.name} paid {value} {resource}.")

    def _handle_discard_card(self, params: Dict[str, Any], source_player: 'Player'):
        """Handles DISCARD_CARD action - discard cards from player's hand."""
        deck_type = params.get("deck", "basic")
        count = params.get("count", 1)
        
        logging.info(f"{source_player.name} discards {count} card(s) from {deck_type} deck")
        # Basic implementation - in a real game, this would involve player choice
        # For now, just log the action

    def _handle_draw_card(self, params: Dict[str, Any], source_player: 'Player'):
        """Handles DRAW_CARD action - draw cards from deck to player's hand."""
        deck_type = params.get("deck", "basic")
        count = params.get("count", 1)
        
        logging.info(f"{source_player.name} draws {count} card(s) from {deck_type} deck")
        # Basic implementation - in a real game, this would involve actual card drawing logic

    def _handle_lookup(self, params: Dict[str, Any], source_player: 'Player'):
        """Handles LOOKUP action - view opponent's hand or other information."""
        target_str = params.get("target", "OPPONENT_CHOICE_SINGLE")
        info_type = params.get("info_type", "hand_cards")
        
        targets = self._get_targets(target_str, source_player)
        for target in targets:
            logging.info(f"{source_player.name} looks up {info_type} of {target.name}")
        # Basic implementation - in a real game, this would reveal actual information

    def _handle_create_entity(self, params: Dict[str, Any], source_player: 'Player'):
        """Handles CREATE_ENTITY action - create new entities on the board."""
        entity_type = params.get("entity_type", "token")
        count = params.get("count", 1)
        
        logging.info(f"{source_player.name} creates {count} {entity_type} entity/entities")
        # Basic implementation - in a real game, this would create actual game entities

    def _handle_transfer_resource(self, params: Dict[str, Any], source_player: 'Player'):
        """Handles TRANSFER_RESOURCE action - transfer resources between players."""
        target_str = params.get("target", "OPPONENT_CHOICE_SINGLE")
        resource = params.get("resource", "gold")
        value = self._resolve_value(params.get("value"), source_player)
        
        targets = self._get_targets(target_str, source_player)
        for target in targets:
            logging.info(f"{source_player.name} transfers {value} {resource} to {target.name}")
            # Basic implementation - in a real game, this would actually transfer resources

    def _handle_unimplemented(self, params: Dict[str, Any], source_player: 'Player', action_type: str = "Unknown"):
        logging.warning(f"Action '{action_type}' is not yet implemented.")

    # --- Private Helper Methods for Execution Flow ---

    def _check_condition(self, condition: Dict[str, Any], source_player: 'Player') -> bool:
        """Checks if a condition is met."""
        # This is a stub. A full implementation would be a recursive evaluator.
        op = condition.get("op")
        if op == "GREATER_THAN":
            # Simplified example: { "op": "GREATER_THAN", "a": {"var": "SELF_YANG"}, "b": 3 }
            # For now, we don't resolve complex variables, just return a default
            logging.info("'GREATER_THAN' condition check is a stub. Defaulting to TRUE.")
            return True
        logging.warning(f"Condition operator '{op}' not implemented. Defaulting to TRUE.")
        return True

    def _pay_costs(self, costs: List[Dict[str, Any]], source_player: 'Player') -> bool:
        """
        Checks if a player can afford all costs and then pays them.
        This is NOT atomic. If a player can pay the first cost but not the second,
        the first is still paid. A real implementation would need a temporary state
        and a final commit/rollback.
        """
        # 1. Check affordability
        for cost_data in costs:
            resource = cost_data.get("resource")
            value = self._resolve_value(cost_data.get("value"), source_player)
            if not source_player.can_afford(resource, value):
                logging.warning(f"Affordability check failed: Cannot pay {value} {resource}.")
                return False

        # 2. Pay costs
        for cost_data in costs:
            resource = cost_data.get("resource")
            value = self._resolve_value(cost_data.get("value"), source_player)
            source_player.change_resource(resource, -value)
            logging.debug(f"Cost Paid: {source_player.name} paid {value} {resource}.")
        return True