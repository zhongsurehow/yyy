# Tianji Bian - Game Rules

This document outlines the core rules and mechanics of the Tianji Bian game engine.

## 1. Game Objective

The primary goal is to be the last player remaining on the board. If the game reaches its round limit (currently 10 rounds), the winner is the player with the most wealth, calculated first by Gold and then by Health.

## 2. Phases of a Round

Each round of the game is divided into six distinct phases, executed in order:

1.  **Time (天时) Phase**: The celestial stems and terrestrial branches for the round are drawn, determining the elemental influences on the board.
2.  **Placement (布局) Phase**: Players have the opportunity to play cards and use abilities. (Note: Player actions are not yet fully implemented in the current prototype).
3.  **Movement (行动) Phase**: Players move on the board according to a set of rules, potentially triggering duels.
4.  **Interpretation (解局) Phase**: (Reserved for future mechanics).
5.  **Resolution (结算) Phase**: The effects of the board's elemental energies are applied to the players based on their location.
6.  **Upkeep (整备) Phase**: Status effects are updated, cards are discarded, and the game prepares for the next round.

## 3. Core Mechanics: The Cosmic Engine

The strategic landscape of the board is in constant flux, governed by a multi-layered system based on the Chinese calendar and metaphysics. This system advances automatically at the start of each new round (after the first round concludes).

### 3.1. Seasonal Progression: Solar Terms and Dun Cycles

The game's clock is the **24 Solar Terms (二十四节气)**.
- At the beginning of each new round, the game advances to the next solar term in the cycle (e.g., from Winter Solstice to Lesser Cold).
- The current solar term determines whether the round operates under the **Yang Dun (阳遁)** or **Yin Dun (阴遁)** cycle. This is the most critical factor for the round's setup.
  - **Yang Dun Cycle**: Active from the Winter Solstice (冬至) to the Summer Solstice (夏至).
  - **Yin Dun Cycle**: Active from the Summer Solstice (夏至) back to the Winter Solstice (冬至).

### 3.2. Plate Calculation: The Qi Men Ju (奇门局)

At the start of each round, the engine uses the current solar term and its Dun cycle to calculate the **Ju (局)**, or "plate layout number," for the round. This number dictates the positions of the Eight Gates.

-   **Ju Calculation**: The calculation is based on the solar term's position within its 12-term Dun cycle.
    -   For **Yang Dun**, the Ju number cycles from 1 to 9. For example, the first solar term of the Yang cycle (Winter Solstice) uses **Yang Ju 1 (阳遁一局)**.
    -   For **Yin Dun**, the Ju number cycles in reverse, from 9 to 1. For example, the first solar term of the Yin cycle (Summer Solstice) uses **Yin Ju 9 (阴遁九局)**.

### 3.3. The Eight Gates (八门)

The calculated Ju number determines the placement of the eight gates (休, 生, 伤, 杜, 景, 死, 惊, 开) on the eight palaces of the game board. Each gate has a distinct effect and is classified as either **Auspicious (吉门)**, **Inauspicious (凶门)**, or **Neutral (中平门)**. These effects are triggered when a player ends their movement in a palace, making the gate layout a core strategic element of the game.

## 4. Movement and Duels

-   **Movement**: Players move between the three rings of the board (Tian, Ren, Di) based on a fixed set of rules. For example, a player in a Di (地) zone can move to the Ren (人) zone of the same palace or to the Di zones of adjacent palaces.
-   **Duels (论道)**: If a player moves into a zone already occupied by another player, a duel is triggered. The duel is resolved by comparing the stroke counts of the players' lowest-stroke basic cards. The winner takes a small amount of gold from the loser.