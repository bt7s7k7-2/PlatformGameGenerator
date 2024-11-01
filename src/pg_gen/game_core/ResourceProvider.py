import pygame
import pygame.freetype

from ..support.Point import Point
from .Texture import Texture


class ResourceProvider:
    def __init__(self) -> None:
        self.font = pygame.freetype.SysFont("Arial", 12)

        spritesheet = Texture(
            pygame.image.load("./assets/spritesheet.png").convert_alpha(),
        )

        self.key_sprite = spritesheet.slice(Point(32, 0), Point(16, 16))
        self.door_sprite = spritesheet.slice(Point(0, 0), Point(32, 32))
        self.wall_sprite = spritesheet.slice(Point(32, 16), Point(16, 16))
        self.ladder_sprite = spritesheet.slice(Point(48, 16), Point(16, 16))
        self.pole_sprite = spritesheet.slice(Point(48, 32), Point(16, 16))
        self.skull_sprite = spritesheet.slice(Point(32, 32), Point(16, 16))
        self.player_sprite = spritesheet.slice(Point(48, 0), Point(16, 16))
        self.bobber_sprite = spritesheet.slice(Point(0, 32), Point(16, 16))

        self.fire = [spritesheet.slice(Point(x * 16, 48), Point(16, 16)) for x in range(4)]
        self.fire = [*reversed(self.fire)]

    __singleton_service__ = True
