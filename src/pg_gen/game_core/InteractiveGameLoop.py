from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from .Universe import Universe


class InteractiveGameLoop:

    def run(self):
        pygame.init()

        surface = pygame.display.set_mode((500, 500), flags=pygame.RESIZABLE)
        fps_keeper = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                pass
            pass

            world = self.universe.world
            if world is not None:
                world.draw(surface)

            pygame.display.update()
            fps_keeper.tick(60)
        pass

    def __init__(self, universe: "Universe"):
        self.universe = universe
        pass
