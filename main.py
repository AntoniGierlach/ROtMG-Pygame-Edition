import pygame
import sys
from game import Game

def main():
    """
    Inicjalizuje Pygame, tworzy instancję Game i uruchamia ją.
    Po zakończeniu zwalnia zasoby i kończy program.
    """
    pygame.init()
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()