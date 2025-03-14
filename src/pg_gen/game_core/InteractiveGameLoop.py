import time
from datetime import datetime
from typing import TYPE_CHECKING, override

import pygame

from ..support.constants import CAMERA_SCALE, ROOM_HEIGHT, ROOM_WIDTH
from .GameLoop import GameLoop
from .InputState import InputState

if TYPE_CHECKING:
    from .Universe import Universe


class InteractiveGameLoop(GameLoop):

    allow_termination = True
    disable_input_clearing = False
    game_over_reached = False

    @override
    def game_over(self):
        self.game_over_reached = True

    def run(self):
        while True:
            should_terminate = self.run_frame()
            if should_terminate:
                return

    def handle_input(self):
        if not self.disable_input_clearing:
            self.input.clear()

        for event in pygame.event.get():
            self.input.events.append(event)

            if event.type == pygame.QUIT:
                if self.allow_termination:
                    pygame.quit()
                    return True

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                pygame.image.save(self.surface, datetime.now().isoformat() + ".png")

        keys = pygame.key.get_pressed()

        self.input.keys = keys

        self.input.up |= keys[pygame.K_w]
        self.input.left |= keys[pygame.K_a]
        self.input.right |= keys[pygame.K_d]
        self.input.down |= keys[pygame.K_s]
        self.input.jump |= keys[pygame.K_SPACE]

        return self.game_over_reached

    def update_time(self):
        now = time.monotonic()
        delta_time = now - self.start_time
        self.start_time = now

        if delta_time > 1 / 30:
            delta_time = 1 / 30

        return delta_time

    def run_frame(self):
        should_terminate = self.handle_input()
        if should_terminate:
            return True

        self.update_and_render(self.update_time())
        pygame.display.update()
        self.fps_keeper.tick(60)

        return False

    def __init__(self, universe: "Universe"):
        surface = pygame.display.set_mode((CAMERA_SCALE * ROOM_WIDTH, CAMERA_SCALE * ROOM_HEIGHT))
        super().__init__(surface, universe)
        self.fps_keeper = pygame.time.Clock()

        self.input = self.universe.di.inject(InputState)
        self.start_time = time.monotonic()
        pass
