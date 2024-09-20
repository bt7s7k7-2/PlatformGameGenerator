import pygame
from pygame.locals import *


def main():
    pygame.init()

    surface = pygame.display.set_mode((500, 500), flags=RESIZABLE)
    fps_keeper = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return 0
            pass
        pass

        surface.fill((255, 255, 255))

        pygame.draw.circle(surface, (255, 0, 0), (200, 200), 100, width=1)

        pygame.display.update()
        fps_keeper.tick(60)
    pass
