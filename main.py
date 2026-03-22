"""Void Survivors - A top-down space arena survival shooter.

Run this file to start the game:
    python main.py

Controls:
    WASD / Arrow Keys  - Move
    Mouse              - Aim
    Left Click / Space - Shoot
    R                  - Restart (after game over)
    Q                  - Quit (after game over)
"""

from game import Game


def main():
    """Create and run the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
