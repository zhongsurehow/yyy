# Tianji Bian - Web Application (天机变)

Welcome to the Tianji Bian web application. This project is a Python-based, interactive web version of a board game inspired by ancient Chinese metaphysics, including the I Ching (易经), Qi Men Dun Jia (奇门遁甲), and the Five Elements (五行).

The application provides a fully playable two-person game, rendering the complex mechanics of the game in a user-friendly, browser-based interface.

## Features

- **Turn-based Gameplay**: The game progresses in rounds, with each round divided into distinct phases (Time, Placement, Movement, etc.).
- **Dynamic Game Board**: The board state changes each round based on the shifting celestial energies (Stems and Branches).
- **Qi Men Dun Jia Integration**: The auspicious and inauspicious nature of different locations is determined by the shifting Qi Men gates, which are calculated based on the in-game solar term.
- **Card-driven Actions**: Players use cards from their hands to trigger effects, engage in duels, and influence the game.
- **Web-based Interactive Game**: Play the game directly in your browser with a full graphical interface and real-time updates.
- **Phase-by-Phase Control**: Step through the game's phases at your own pace, making it easy to learn the rules and strategies.
- **Detailed Game Log**: A comprehensive log tracks every action and event, providing a clear narrative of the game's progression.

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

### How to Run the Web Application

To run the web application, execute the `server.py` script from the root directory:

```bash
python server.py
```

This will start the web server. You can then access the game by opening your web browser and navigating to:

**http://127.0.0.1:5000**

You can start, play, and reset the game using the controls on the web page.

### How to Run Tests

The project uses `pytest` for testing. To run the test suite, use the following command from the root directory:

```bash
python -m pytest src/
```

This will discover and run all tests located in the `src/` directory.