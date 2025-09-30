import json
import os
from pathlib import Path

def consolidate_cards():
    card_data_path = Path("tianji-fix-data-and/assets/data/cards")
    all_cards = []

    print(f"Scanning for JSON files in {card_data_path}...")
    json_files = list(card_data_path.rglob("*.json"))
    print(f"Found {len(json_files)} card files.")

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_cards.append(data)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    output_path = Path("tianji-fix-data-and/assets/data/cards.json")
    print(f"Writing {len(all_cards)} cards to {output_path}...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_cards, f, ensure_ascii=False, indent=2)
        print("Successfully created consolidated cards.json file.")
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")

if __name__ == "__main__":
    consolidate_cards()