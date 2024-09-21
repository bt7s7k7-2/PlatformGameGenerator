from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from pygame import Surface

from ..support.Point import Point

if TYPE_CHECKING:
    from ..game_core.Universe import Universe
    from .World import World


class CollisionType(Enum):
    NONE = 0
    PLAYER = 1
    STATIC = 2
    TRIGGER = 3


@dataclass(eq=False)
class Actor:
    universe: "Universe" = field(repr=False)
    position: Point = Point.ZERO
    size: Point = Point.ONE
    collision_type: CollisionType = CollisionType.NONE
    world: "World | None" = field(repr=False, init=False)

    def draw(self, surface: Surface): ...
    def update(self, delta: float): ...

    def on_collision(self, collision_object: "Actor"): ...
    def on_trigger(self, trigger: "Actor"): ...

    def remove(self):
        if self.world is None:
            return
        self.world.remove_actor(self)
