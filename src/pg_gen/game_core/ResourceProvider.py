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
        self.door_sprite = spritesheet.slice(Point(0, 0), Point(32, 48))
        self.wall_sprite = spritesheet.slice(Point(32, 16), Point(16, 16))

        pass

    __singleton_service__ = True
