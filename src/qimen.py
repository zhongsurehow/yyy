# src/qimen.py

"""
This module defines the data and logic for the Qi Men Dun Jia system,
including the distribution of the Eight Gates (八门) across the palaces
for each Ju (局) and the effects associated with each gate.

The logic for determining the Ju number is a simplified game mechanic
and not a traditional calendrical calculation.
"""

# --- Gate Distribution Map (阳遁九局八门分布图) ---
# Maps Ju number -> Palace Name -> Gate ID
# This represents the fixed layout of the gates for each of the 9 Ju in the Yang Dun cycle.
YANG_JU_GATE_DISTRIBUTION = {
    1: {"kan": "休", "gen": "生", "zhen": "伤", "xun": "杜", "li": "景", "kun": "死", "dui": "惊", "qian": "开"},
    2: {"kan": "死", "gen": "惊", "zhen": "开", "xun": "休", "li": "生", "kun": "伤", "dui": "杜", "qian": "景"},
    3: {"kan": "景", "gen": "死", "zhen": "惊", "xun": "开", "li": "休", "kun": "生", "dui": "伤", "qian": "杜"},
    4: {"kan": "杜", "gen": "景", "zhen": "死", "xun": "惊", "li": "开", "kun": "休", "dui": "生", "qian": "伤"},
    5: {"kan": "伤", "gen": "杜", "zhen": "景", "xun": "死", "li": "惊", "kun": "开", "dui": "休", "qian": "生"},
    6: {"kan": "开", "gen": "休", "zhen": "生", "xun": "伤", "li": "杜", "kun": "景", "dui": "死", "qian": "惊"},
    7: {"kan": "生", "gen": "伤", "zhen": "杜", "xun": "景", "li": "死", "kun": "惊", "dui": "开", "qian": "休"},
    8: {"kan": "惊", "gen": "开", "zhen": "休", "xun": "生", "li": "伤", "kun": "杜", "dui": "景", "qian": "死"},
    9: {"kan": "伤", "gen": "杜", "zhen": "景", "xun": "死", "li": "惊", "kun": "开", "dui": "休", "qian": "生"},
}

# --- Gate Distribution Map (阴遁九局八门分布图) ---
# Maps Ju number -> Palace Name -> Gate ID
# This represents the fixed layout of the gates for each of the 9 Ju in the Yin Dun cycle.
YIN_JU_GATE_DISTRIBUTION = {
    9: {"kan": "休", "gen": "生", "zhen": "伤", "xun": "杜", "li": "景", "kun": "死", "dui": "惊", "qian": "开"},
    8: {"kan": "开", "gen": "休", "zhen": "生", "xun": "伤", "li": "杜", "kun": "景", "dui": "死", "qian": "惊"},
    7: {"kan": "惊", "gen": "开", "zhen": "休", "xun": "生", "li": "伤", "kun": "杜", "dui": "景", "qian": "死"},
    6: {"kan": "死", "gen": "惊", "zhen": "开", "xun": "休", "li": "生", "kun": "伤", "dui": "杜", "qian": "景"},
    5: {"kan": "景", "gen": "死", "zhen": "惊", "xun": "开", "li": "休", "kun": "生", "dui": "伤", "qian": "杜"},
    4: {"kan": "杜", "gen": "景", "zhen": "死", "xun": "惊", "li": "开", "kun": "休", "dui": "生", "qian": "伤"},
    3: {"kan": "生", "gen": "伤", "zhen": "杜", "xun": "景", "li": "死", "kun": "惊", "dui": "开", "qian": "休"},
    2: {"kan": "伤", "gen": "杜", "zhen": "景", "xun": "死", "li": "惊", "kun": "开", "dui": "休", "qian": "生"},
    1: {"kan": "景", "gen": "死", "zhen": "惊", "xun": "开", "li": "休", "kun": "生", "dui": "伤", "qian": "杜"},
}


# --- Gate Effects (八门效果) ---
# Defines the effect triggered when a player ends their movement in a palace with a specific gate.
# This structure is designed to be parsed by the EffectEngine.
GATE_EFFECTS = {
    # 吉门 (Auspicious Gates)
    "开": {
        "name": "开门 (Open Gate)",
        "type": "Auspicious",
        "effect": {
            "actions": [
                {"action": "GAIN_RESOURCE", "params": {"target": "SELF", "resource": "gold", "value": 5}},
                {"action": "DRAW_CARD", "params": {"target": "SELF", "deck": "function", "count": 1}}
            ]
        }
    },
    "休": {
        "name": "休门 (Rest Gate)",
        "type": "Auspicious",
        "effect": {
            "actions": [
                {"action": "GAIN_RESOURCE", "params": {"target": "SELF", "resource": "health", "value": 10}},
            ]
        }
    },
    "生": {
        "name": "生门 (Life Gate)",
        "type": "Auspicious",
        "effect": {
            "actions": [{
                "action": "CHOICE",
                "params": {
                    "target": "SELF",
                    "options": [
                        {"description": "获得10金币", "effect": {"actions": [{"action": "GAIN_RESOURCE", "params": {"target": "SELF", "resource": "gold", "value": 10}}]}},
                        {"description": "回复15生命值", "effect": {"actions": [{"action": "GAIN_RESOURCE", "params": {"target": "SELF", "resource": "health", "value": 15}}]}}
                    ]
                }
            },
            ]
        }
    },
    # 中平门 (Neutral Gates)
    "景": {
        "name": "景门 (View Gate)",
        "type": "Neutral",
        "effect": {
            "actions": [
                {"action": "LOOKUP", "params": {"target": "OPPONENT_CHOICE_SINGLE", "info_type": "hand_cards"}}
            ]
        }
    },
    "杜": {
        "name": "杜门 (Delusion Gate)",
        "type": "Neutral",
        "effect": {
             "actions": [
                {"action": "APPLY_STATUS", "params": {"target": "SELF", "status_id": "GATE_DU_IMMUNITY", "duration": 1}}
             ]
        }
    },
    # 凶门 (Inauspicious Gates)
    "惊": {
        "name": "惊门 (Fear Gate)",
        "type": "Inauspicious",
        "effect": {
            "actions": [
                {"action": "DISCARD_CARD", "params": {"target": "SELF", "deck": "function", "count": 1}}
            ]
        }
    },
    "伤": {
        "name": "伤门 (Harm Gate)",
        "type": "Inauspicious",
        "effect": {
            "actions": [
                {"action": "LOSE_RESOURCE", "params": {"target": "SELF", "resource": "health", "value": 10}}
            ]
        }
    },
    "死": {
        "name": "死门 (Death Gate)",
        "type": "Inauspicious",
        "effect": {
            "actions": [
                {"action": "LOSE_RESOURCE", "params": {"target": "SELF", "resource": "gold", "value": 10}}
            ]
        }
    },
}

def get_ju_number_for_solar_term(solar_term_index: int, dun_type: str) -> int:
    """
    Calculates the Ju number based on the solar term's position within its Dun.
    This is a simplified game rule, not a traditional calendrical calculation.

    Args:
        solar_term_index: The index (0-23) of the current solar term in the yearly cycle.
        dun_type: A string, either "YANG" or "YIN", indicating the current Dun cycle.

    Returns:
        The calculated Ju number (1-9).
    """
    # Each Dun cycle (Yin and Yang) contains 12 solar terms.
    # The position within the current Dun determines the starting point for the Ju calculation.
    position_in_dun = solar_term_index % 12

    # This simplified logic maps the 12 positions to 9 Ju numbers, repeating the cycle.
    # For example, in Yang Dun, the 1st, 10th, and 19th solar terms all use Yang Ju 1.
    if dun_type == "YANG":
        # Yang Dun Ju cycles 1, 2, 3, ... 9
        return (position_in_dun % 9) + 1
    else:  # YIN
        # Yin Dun Ju cycles 9, 8, 7, ... 1
        return 9 - (position_in_dun % 9)

def get_gate_layout_for_ju(ju_number: int, dun_type: str) -> dict:
    """
    Returns the gate distribution map for a given Ju number and Dun type.

    Args:
        ju_number: The Ju number (1-9) for which to get the gate layout.
        dun_type: A string, either "YANG" or "YIN".

    Returns:
        A dictionary mapping palace IDs to gate symbols (e.g., {"kan": "休"}).
    """
    distribution_map = None
    if dun_type == "YANG":
        distribution_map = YANG_JU_GATE_DISTRIBUTION
    elif dun_type == "YIN":
        distribution_map = YIN_JU_GATE_DISTRIBUTION

    if distribution_map:
        # The Ju number should already be within 1-9, but we use .get() for safety.
        return distribution_map.get(ju_number, {})
    return {}

def get_effect_for_gate(gate_name: str) -> dict | None:
    """Returns the effect JSON for a given gate name."""
    return GATE_EFFECTS.get(gate_name, {}).get("effect")