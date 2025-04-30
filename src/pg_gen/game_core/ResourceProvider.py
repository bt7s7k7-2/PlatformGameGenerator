import pygame
import pygame.freetype

from ..assets import get_pg_assets
from ..support.Point import Point
from .Texture import Texture


class ResourceProvider:
    def __init__(self) -> None:
        assets = get_pg_assets()

        self.font = pygame.freetype.SysFont("Arial", 12)
        self.display_font = pygame.freetype.Font(str(assets.font), 120)

        spritesheet = Texture(
            pygame.image.load(str(assets.spritesheet)).convert_alpha(),
        )

        self.key_sprite = spritesheet.slice(Point(32, 0), Point(16, 16))
        self.door_sprite = spritesheet.slice(Point(0, 0), Point(32, 32))
        self.wall_sprite = spritesheet.slice(Point(32, 16), Point(16, 16))
        self.ladder_sprite = spritesheet.slice(Point(48, 16), Point(16, 16))
        self.pole_sprite = spritesheet.slice(Point(48, 32), Point(16, 16))
        self.skull_sprite = spritesheet.slice(Point(32, 32), Point(16, 16))
        self.player_sprite = spritesheet.slice(Point(48, 0), Point(16, 16))
        self.bobber_sprite = spritesheet.slice(Point(0, 32), Point(16, 16))
        self.gem_sprite = spritesheet.slice(Point(16, 32), Point(16, 16))
        self.eye_sprite = spritesheet.slice(Point(64, 32), Point(16, 16))

        self.fire = [spritesheet.slice(Point(x * 16, 48), Point(16, 16)) for x in range(4)]
        self.fire = [*reversed(self.fire)]

        self.portal = [spritesheet.slice(x, Point(48, 48)) for x in [Point(0, 112), Point(48, 64), Point(0, 64)]]
        self.empty_portal = spritesheet.slice(Point(48, 112), Point(48, 48))

        self.blocker = [spritesheet.slice(Point(64, x * 16), Point(16, 16)) for x in range(2)]

    __singleton_service__ = True
