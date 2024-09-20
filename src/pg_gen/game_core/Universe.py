from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..world.World import World

from .DependencyInjection import DependencyInjection


class Universe:
    world: "World | None" = None

    def __init__(self):
        self.di = DependencyInjection()
        pass
