import logging
from ..game_state import GameState
from ..player import Player
from ..card import Card

# Get the story_logger from the root of the game
story_logger = logging.getLogger("story_logger")

def _choose_best_card_to_play(player: Player) -> Card | None:
    """A simple AI to choose a card to play based on the player's situation."""
    basic_cards = [c for c in player.hand if c.card_type == 'basic']
    if not basic_cards:
        return None

    # Heuristic: choose the card with the fewest strokes, as it's good for duels.
    best_card = min(basic_cards, key=lambda card: card.strokes)

    story_logger.info(f"  - {player.name} thinks about which card to play...")
    story_logger.info(f"  - They choose '{best_card.name}' because its low stroke count ({best_card.strokes}) is advantageous in duels (Lun Dao).")

    return best_card

def execute(game_state: GameState):
    """
    Executes the logic for the PLACEMENT phase of the game.
    - Each player chooses a card to play face down.
    """
    game_state.set_phase("PLACEMENT")
    story_logger.info("\n--- Placement Phase ---")
    story_logger.info("Players decide which card to commit to this round's interpretation.")

    for player in game_state.players:
        if player.is_eliminated:
            continue

        card_to_play = _choose_best_card_to_play(player)

        if card_to_play:
            player.play_card(card_to_play.card_id)
            story_logger.info(f"  - {player.name} places '{card_to_play.name}' face down.")
            logging.info(f"{player.name} 放置卡牌: {card_to_play.name} (面朝下)")
        else:
            story_logger.info(f"  - {player.name} has no basic cards to play this turn.")
            logging.info(f"{player.name} 没有基本卡牌可放置")