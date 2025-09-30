import logging
from .. import five_elements as fe
from .. import qimen as qm
from ..game_state import GameState

# Get the story_logger from the root of the game
story_logger = logging.getLogger("story_logger")

def execute(game_state: GameState, game_instance):
    """
    Executes the logic for the TIME phase of the game.
    - Determines celestial influences.
    - Updates Qi Men gates.
    - Draws new time cards.
    - Calculates beneficial/harmful elements.
    """
    game_state.set_phase("TIME")
    dun_type = game_state.dun_type
    dun_text = "Yang" if dun_type == "YANG" else "Yin"
    solar_term_name = game_state.current_solar_term.name
    ju_number = qm.get_ju_number_for_solar_term(game_state.solar_term_index, dun_type)

    story_logger.info(f"\n--- Time Phase ---")
    story_logger.info(f"The celestial energies shift. It is now the '{solar_term_name}' solar term.")
    story_logger.info(f"This is a {dun_text} Dun period, corresponding to Ju {ju_number}.")
    logging.info(f"当前节气: {solar_term_name} ({dun_text}遁), 第{ju_number}局")

    # This still needs access to the game instance to call _update_qimen_gates
    game_instance._update_qimen_gates()

    if game_state.current_celestial_stem:
        logging.info(f"弃置天干牌: {game_state.current_celestial_stem.name}")
        game_state.celestial_stem_discard_pile.append(game_state.current_celestial_stem)
    if game_state.current_terrestrial_branch:
        logging.info(f"弃置地支牌: {game_state.current_terrestrial_branch.name}")
        game_state.terrestrial_branch_discard_pile.append(game_state.current_terrestrial_branch)

    game_instance._reshuffle_if_needed('celestial_stem')
    game_instance._reshuffle_if_needed('terrestrial_branch')

    if not game_state.celestial_stem_deck or not game_state.terrestrial_branch_deck:
        logging.error("Critical: Cannot draw new time cards. Decks are empty.")
        return

    game_state.current_celestial_stem = game_state.celestial_stem_deck.pop()
    game_state.current_terrestrial_branch = game_state.terrestrial_branch_deck.pop()
    story_logger.info(f"The new time cards are '{game_state.current_celestial_stem.name}' and '{game_state.current_terrestrial_branch.name}'.")

    stem_element = fe.get_element_for_stem(game_state.current_celestial_stem.card_id.split('_')[-1])
    branch_element = fe.get_element_for_branch(game_state.current_terrestrial_branch.card_id.split('_')[-1])

    beneficial_elements = {fe.get_generated_element(stem_element), fe.get_generated_element(branch_element)}
    harmful_elements = {fe.get_overcome_element(stem_element), fe.get_overcome_element(branch_element)}
    story_logger.info(f"This makes {beneficial_elements} beneficial and {harmful_elements} harmful this round.")

    for zone in game_state.game_board.zones.values():
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