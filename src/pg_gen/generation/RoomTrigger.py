from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pygame
from pygame import Surface

from ..entities.Player import Player
from ..support.Color import Color
from ..support.constants import CAMERA_SCALE
from ..support.Direction import Direction
from ..world.Actor import Actor
from ..world.CollisionFlags import CollisionFlags

if TYPE_CHECKING:
    from .RoomController import RoomController


@dataclass
class RoomTrigger(Actor):
    collision_flags: CollisionFlags = field(default=CollisionFlags.TRIGGER)
    room_controller: "RoomController" = field(default=None, repr=False)  # type: ignore
    direction: Direction = field(default=Direction.UP)

    def on_trigger(self, trigger: Actor):
        if not isinstance(trigger, Player):
            return

        self.room_controller.switch_rooms(self.direction)

    def draw(self, surface: Surface):
        pygame.draw.rect(
            surface,
            color=Color.GREEN.to_pygame_color(),
            rect=self.position.to_pygame_rect(self.size, CAMERA_SCALE),
            width=1,
        )
