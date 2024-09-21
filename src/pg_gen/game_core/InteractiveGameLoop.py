import time
from typing import TYPE_CHECKING

import pygame

from .InputState import InputState

if TYPE_CHECKING:
    from .Universe import Universe


class InteractiveGameLoop:

    def run(self):
        pygame.init()

        surface = pygame.display.set_mode((500, 500), flags=pygame.RESIZABLE)
        fps_keeper = pygame.time.Clock()

        input = self.universe.di.inject(InputState)
        start_time = time.monotonic()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                pass
            pass

            now = time.monotonic()
            delta_time = now - start_time
            start_time = now

            if delta_time > 1 / 30:
                delta_time = 1 / 30

            keys = pygame.key.get_pressed()

            input.up = keys[pygame.K_w]
            input.left = keys[pygame.K_a]
            input.right = keys[pygame.K_d]
            input.down = keys[pygame.K_s]
            input.jump = keys[pygame.K_SPACE]
            input.show_map = keys[pygame.K_m]

            world = self.universe.world
            if world is not None:
                world.update(delta_time)
                world.draw(surface)

            pygame.display.update()
            fps_keeper.tick(60)
        pass

    def __init__(self, universe: "Universe"):
        self.universe = universe
        pass
