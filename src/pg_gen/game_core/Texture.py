from dataclasses import astuple, dataclass
from functools import cached_property

import pygame
from pygame import Surface

from ..support.Point import Point


@dataclass
class Texture:
    surface: Surface

    def slice(self, point: Point, size: Point):
        result = Surface(astuple(size), flags=pygame.SRCALPHA)
        result.blit(self.surface, (0, 0), point.to_pygame_rect(size))
        return Texture(surface=result)

    @cached_property
    def size(self):
        w, h = self.surface.get_size()
        return Point(w, h)
