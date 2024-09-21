from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pygame import Surface

from pg_gen.world.CollisionFlags import CollisionFlags

from ..support.Point import Point

if TYPE_CHECKING:
    from ..game_core.Universe import Universe
    from .World import World


@dataclass(eq=False)
class Actor:
    universe: "Universe" = field(repr=False)
    position: Point = Point.ZERO
    size: Point = Point.ONE
    collision_flags: CollisionFlags = field(default=CollisionFlags(0), repr=False)
    world: "World | None" = field(repr=False, init=False)

    def draw(self, surface: Surface): ...
    def update(self, delta: float): ...

    def on_trigger(self, trigger: "Actor"): ...

    def remove(self):
        if self.world is None:
            return
        self.world.remove_actor(self)
