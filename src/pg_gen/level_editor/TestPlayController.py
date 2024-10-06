from dataclasses import dataclass
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ..world.World import World

from ..game_core.InputClient import InputClient


@dataclass
class TestPlayController(InputClient):
    editor_world: "World" = None  # type: ignore

    def update(self, delta: float):
        was_enter_pressed = any(event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN for event in self._input.events)

        if was_enter_pressed:
            self.universe.queue_task(lambda: self.universe.set_world(self.editor_world))
