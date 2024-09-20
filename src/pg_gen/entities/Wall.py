from dataclasses import astuple, dataclass
from typing import override

import pygame
from pygame import Surface

from ..support.Color import Color
from ..world.Actor import Actor


@dataclass
class Wall(Actor):
    color: Color = Color.WHITE

    @override
    def draw(self, surface: Surface):
        pygame.draw.rect(
            surface,
            color=astuple(self.color),
            rect=(*astuple(self.position), *astuple(self.size)),
        )
