from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..generation.MapGenerator import MapGenerator
    from ..world.World import World

from .DependencyInjection import DependencyInjection


class Universe:
    world: "World | None" = None

    def __init__(self, map: "MapGenerator"):
        self.di = DependencyInjection()
        self.map = map
        pass
