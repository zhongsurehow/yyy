import json
from pathlib import Path
from typing import List, Dict

from .card import Card

class GameLoader:
    """Handles loading all game data from the file system."""

    def __init__(self, assets_path: Path):
        """Initializes the loader with the path to the assets directory."""
        self.assets_path = assets_path
        if not self.assets_path.exists():
            raise FileNotFoundError(f"Assets directory not found at '{self.assets_path}'")

    def load_all_cards(self) -> Dict[str, List[Card]]:
        """
        Loads all card data from the consolidated `assets/data/cards.json` file.

        Returns:
            A dictionary mapping deck type (e.g., "basic", "function") to a list of Card objects.
        """
        decks = {
            "basic": [],
            "function": [],
            "destiny": [],
            "natal": [],
            "state": [],
            "celestial_stem": [],
            "terrestrial_branch": []
        }
        card_data_path = self.assets_path / "data" / "cards.json"

        print("--- Loading Card Data from Consolidated File ---")
        if not card_data_path.is_file():
            print(f"Error: Consolidated card data file not found at '{card_data_path}'")
            return decks

        try:
            with open(card_data_path, 'r', encoding='utf-8') as f:
                all_card_data = json.load(f)

            print(f"Found {len(all_card_data)} cards to load.")

            for data in all_card_data:
                card = Card.from_json(data)
                card_type = card.card_type

                if card_type in decks:
                    decks[card_type].append(card)
                elif card_type == "stem":
                    decks["celestial_stem"].append(card)
                elif card_type == "branch":
                    decks["terrestrial_branch"].append(card)
                elif card_type == "celestial":
                    decks["state"].append(card)
                else:
                    print(f"Warning: Card '{card.card_id}' has unknown type '{card_type}'. Skipping.")

        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {card_data_path}")
        except Exception as e:
            print(f"Error: Failed to load cards from {card_data_path}: {e}")

        print(f"Loaded {len(decks['basic'])} basic cards.")
        print(f"Loaded {len(decks['function'])} function cards.")
        print(f"Loaded {len(decks['destiny'])} destiny cards.")
        print(f"Loaded {len(decks['celestial_stem'])} celestial stem cards.")
        print(f"Loaded {len(decks['terrestrial_branch'])} terrestrial branch cards.")
        print("------------------------------------------")

        return decks