# Tianji Bian - Game Engine Prototype (天机变)

Welcome to the Tianji Bian game engine prototype. This project is a Python-based simulation of a board game inspired by ancient Chinese metaphysics, including the I Ching (易经), Qi Men Dun Jia (奇门遁甲), and the Five Elements (五行).

The current focus of this prototype is to provide a clear and educational simulation of the game's core mechanics, making it an excellent tool for learning how to play.

## Features

- **Turn-based Gameplay**: The game progresses in rounds, with each round divided into distinct phases (Time, Placement, Movement, etc.).
- **Dynamic Game Board**: The board state changes each round based on the shifting celestial energies (Stems and Branches).
- **Qi Men Dun Jia Integration**: The auspicious and inauspicious nature of different locations is determined by the shifting Qi Men gates, which are calculated based on the in-game solar term.
- **Card-driven Actions**: Players use cards from their hands to trigger effects, engage in duels, and influence the game.
- **Tutorial-focused Simulation**: The simulation includes an intelligent AI that makes strategic decisions and a narrative logger that explains the reasoning behind those decisions, helping new players understand the game's flow and strategy.

## Getting Started

### Prerequisites

- Python 3.10+
- `pip` for package management

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install the required dependencies:**
    The necessary Python packages are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

### How to Run the Simulation

To run the tutorial simulation, execute the `main.py` script from the root directory:

```bash
python main.py
```

This will start a two-player, one-round simulation and print a detailed narrative of the game's events to the console.

### How to Run Tests

The project uses `pytest` for testing. To run the test suite, use the following command from the root directory:

```bash
python -m pytest src/
```

This will discover and run all tests located in the `src/` directory.