from dataclasses import astuple, dataclass, field
from typing import Dict

import pygame
import pygame.freetype

from ..support.Color import Color
from ..support.constants import CAMERA_SCALE
from ..support.Point import Point


@dataclass()
class SpriteSheetReference:
    spritesheet: pygame.Surface
    position: Point
    size: Point

    _color_variations: Dict[Color, "SpriteSheetReference"] | None = field(repr=False, default_factory=lambda: None)

    def tinted(self, color: Color):
        if self._color_variations is None:
            self._color_variations = {Color.WHITE: self}

        if color in self._color_variations:
            return self._color_variations[color]

        white = self._color_variations[Color.WHITE]
        tinted_surface = pygame.Surface(astuple(self.size), flags=pygame.SRCALPHA)
        white.draw(tinted_surface, Point.ZERO, 1)
        tinted_surface.fill(color.to_pygame_color(), special_flags=pygame.BLEND_RGB_MULT)
        tinted = SpriteSheetReference(tinted_surface, Point.ZERO, self.size, self._color_variations)
        self._color_variations[color] = tinted
        return tinted

    def draw(self, surface: pygame.Surface, position: Point, scale: float):
        surface.blit(self.spritesheet, position.to_pygame_rect(self.size, scale), self.position.to_pygame_rect(self.size))


class ResourceProvider:

    def __init__(self) -> None:
        self.font = pygame.freetype.SysFont("Arial", 12)

        spritesheet = pygame.image.load("./assets/temp_spritesheet.png").convert_alpha()

        spritesheet_size = spritesheet.get_size()
        pixel_size = CAMERA_SCALE / 16
        spritesheet = pygame.transform.scale(spritesheet, (spritesheet_size[0] * pixel_size, spritesheet_size[1] * pixel_size))

        self.key_sprite = SpriteSheetReference(spritesheet, Point.ZERO, Point(1, 1) * CAMERA_SCALE)
        self.door_sprite = SpriteSheetReference(spritesheet, Point(2, 0) * CAMERA_SCALE, Point(2, 3) * CAMERA_SCALE)

        pass

    __singleton_service__ = True
