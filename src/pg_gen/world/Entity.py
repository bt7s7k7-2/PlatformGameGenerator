from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pygame import Surface

if TYPE_CHECKING:
    from ..game_core.Universe import Universe
    from .World import World


@dataclass(eq=False)
class Entity:
    world: "World" = field(repr=False)
    universe: "Universe" = field(repr=False)

    def draw(self, surface: Surface): ...
    def update(self, delta: float): ...
