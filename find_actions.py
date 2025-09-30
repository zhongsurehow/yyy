import json
from pathlib import Path

def find_unique_actions(data):
    """Recursively finds all values for the key 'action' in a nested structure."""
    actions = set()
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "action":
                if isinstance(value, str):
                    actions.add(value)
            else:
                actions.update(find_unique_actions(value))
    elif isinstance(data, list):
        for item in data:
            actions.update(find_unique_actions(item))
    return actions

def main():
    """
    Parses the consolidated cards.json file to identify all unique action types
    and compares them against the currently implemented actions in the effect engine.
    """
    # Actions currently implemented in effect_engine.py
    implemented_actions = {
        "GAIN_RESOURCE", "LOSE_RESOURCE", "DEAL_DAMAGE", "APPLY_STATUS",
        "REMOVE_STATUS", "MOVE", "CHOICE", "MODIFY_RULE", "INTERRUPT",
        "COPY_EFFECT", "TRIGGER_EVENT", "PAY_COST", "DISCARD_CARD",
        "DRAW_CARD", "LOOKUP", "CREATE_ENTITY", "TRANSFER_RESOURCE"
    }

    card_data_path = Path("tianji-fix-data-and/assets/data/cards.json")
    try:
        with open(card_data_path, 'r', encoding='utf-8') as f:
            all_card_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {card_data_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {card_data_path}")
        return

    all_card_actions = find_unique_actions(all_card_data)

    unimplemented_actions = all_card_actions - implemented_actions

    print("--- Action Implementation Report ---")
    print(f"\nTotal unique actions in card data: {len(all_card_actions)}")
    print(f"Implemented actions in engine: {len(implemented_actions)}")

    if unimplemented_actions:
        print("\nUnimplemented Actions:")
        for action in sorted(list(unimplemented_actions)):
            print(f"- {action}")
    else:
        print("\nAll actions are implemented!")

    print("\n------------------------------------")


if __name__ == "__main__":
    main()