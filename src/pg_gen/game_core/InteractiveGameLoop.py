import time
from typing import TYPE_CHECKING

import pygame

from ..support.constants import CAMERA_SCALE, ROOM_HEIGHT, ROOM_WIDTH
from .Camera import Camera
from .InputState import InputState

if TYPE_CHECKING:
    from .Universe import Universe


class InteractiveGameLoop:

    def run(self):
        pygame.init()

        surface = pygame.display.set_mode((CAMERA_SCALE * ROOM_WIDTH, CAMERA_SCALE * ROOM_HEIGHT))
        camera = Camera(screen=surface)
        self.universe.di.register(Camera, camera)

        fps_keeper = pygame.time.Clock()

        input = self.universe.di.inject(InputState)
        start_time = time.monotonic()

        while True:
            input.events.clear()

            for event in pygame.event.get():
                input.events.append(event)

                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            now = time.monotonic()
            delta_time = now - start_time
            start_time = now

            if delta_time > 1 / 30:
                delta_time = 1 / 30

            keys = pygame.key.get_pressed()

            input.keys = keys

            input.up = keys[pygame.K_w]
            input.left = keys[pygame.K_a]
            input.right = keys[pygame.K_d]
            input.down = keys[pygame.K_s]
            input.jump = keys[pygame.K_SPACE]

            surface.fill((0, 0, 0))

            world = self.universe.world
            if world is not None:
                world.update(delta_time)
                world.draw()

            self.universe.execute_pending_tasks()

            pygame.display.update()
            fps_keeper.tick(60)
        pass

    def __init__(self, universe: "Universe"):
        self.universe = universe
        pass
