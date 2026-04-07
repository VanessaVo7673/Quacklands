"""Legend of the First Flock - Main Entry Point"""

from game import Game
import sys

if __name__ == '__main__':
    game = Game()
    # Start at chapter1 for testing, otherwise start at main_menu
    if '--chapter1' in sys.argv:
        game.current_scene = 'chapter1'
        game.load_ui()
    game.run()

