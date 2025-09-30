# Tianji Bian - Game Rules

This document outlines the rules for the Tianji Bian board game prototype.

## 1. Game Objective

The primary goal in Tianji Bian is to be the last player standing. Players are eliminated if their Health drops to 0 or below. The game is a contest of strategy, resource management, and adapting to the ever-changing celestial energies.

## 2. Game Setup

1.  **Players**: The game can be played by 2 or more players.
2.  **Initial Resources**: Each player starts with:
    - 200 Health
    - 100 Gold
3.  **Starting Hand**: Each player draws a hand of 7 Basic cards.
4.  **Board Initialization**: Players are placed on starting zones on the game board. The initial layout of the Qi Men gates is determined by the first solar term of the game.

## 3. Core Concepts

### 3.1. The Game Board

The board is divided into 25 zones, each associated with one of the Nine Palaces (九宫) and belonging to one of four departments:
- **Tian (天部)**: Heaven Department. These zones often provide rewards (Gold).
- **Di (地部)**: Earth Department. These zones can inflict penalties (Gold).
- **Ren (人部)**: Human Department. These zones are neutral ground.
- **Zhong (中宫)**: The Central Palace, a special zone with its own unique rules (e.g., a 10% Gold tax).

### 3.2. Five Elements (五行)

Each round, two of the five elements (Wood, Fire, Earth, Metal, Water) become **Beneficial**, and two become **Harmful**. This is determined by the Gan-Zhi (干支) time cards drawn during the Time Phase.
- Zones with a **Beneficial** element may offer increased rewards or reduced penalties.
- Zones with a **Harmful** element may have increased penalties or nullified rewards.

### 3.3. Qi Men Dun Jia (奇门遁甲)

The Qi Men Dun Jia system influences the board through the **Eight Gates** (八门). Each of the eight outer palaces is assigned one gate per round.
- **Auspicious Gates** (吉门): Such as 休门 (Rest), 生门 (Life), 开门 (Open). Landing in a zone with an auspicious gate typically provides a positive effect, like restoring health.
- **Inauspicious Gates** (凶门): Such as 伤门 (Harm), 死门 (Death), 惊门 (Fear). Landing in a zone with an inauspicious gate often results in a negative effect.
- The layout of the gates changes each round based on the current **Solar Term** (节气), **Dun Type** (阴阳遁), and **Ju Number** (局数).

### 3.4. Lun Dao (论道) - Duels

If a player moves into a zone already occupied by another player, a duel known as "Lun Dao" is triggered.
1.  Both players select a Basic card from their hand and reveal it.
2.  The player whose card has the **lower stroke count** (笔画数) wins the duel.
3.  The winner steals a small amount of Gold (e.g., 5) from the loser.
4.  If the stroke counts are equal, the duel is a draw.

## 4. Round Structure

Each round of the game consists of six phases, executed in order:

1.  **Time Phase**:
    - The Solar Term may advance.
    - New Gan-Zhi (time) cards are drawn to determine the round's beneficial and harmful elements.
    - The Qi Men gates on the board are updated based on the new time.

2.  **Placement Phase**:
    - All players secretly choose one Basic card from their hand and place it face down. This card will be used in the Interpretation Phase.

3.  **Movement Phase**:
    - In player order, each player moves their character to an adjacent zone on the board.
    - If a player moves to an occupied zone, a **Lun Dao** (duel) occurs immediately.
    - After all movement, the effects of the **Qi Men gates** are triggered for every player based on their new position.

4.  **Interpretation Phase**:
    - Players reveal the cards they placed during the Placement Phase.
    - Card effects are resolved in an order determined by the players' positions on the board (based on Luoshu number and department priority).

5.  **Resolution Phase**:
    - Players receive rewards or pay penalties based on the department (Tian, Di, Zhong) of their current zone.

6.  **Upkeep Phase**:
    - All cards played this round are moved to the discard pile.
    - Status effects are updated (e.g., duration decreases).
    - The turn passes to the next player.

## 5. Winning and Losing

A player is **eliminated** from the game if their Health points reach 0 or less.

There are two ways to win the game:

1.  **Last Player Standing**: If all other players have been eliminated, the last remaining player is declared the winner.

2.  **Victory by Wealth**: If the game reaches a predetermined round limit (e.g., 10 rounds), the simulation ends. The player with the most Gold at that time is declared the winner. In the case of a tie, the player with the higher Health wins.