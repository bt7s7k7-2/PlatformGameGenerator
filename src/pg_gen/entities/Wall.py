from dataclasses import dataclass, field
from typing import override

import pygame
from pygame import Surface

from ..support.Color import Color
from ..support.constants import CAMERA_SCALE
from ..world.Actor import Actor
from ..world.CollisionFlags import CollisionFlags


@dataclass
class Wall(Actor):
    color: Color = Color.WHITE
    collision_flags: CollisionFlags = field(default=CollisionFlags.STATIC)

    @override
    def draw(self, surface: Surface):
        pygame.draw.rect(
            surface,
            color=self.color.to_pygame_color(),
            rect=self.position.to_pygame_rect(self.size, CAMERA_SCALE),
        )
