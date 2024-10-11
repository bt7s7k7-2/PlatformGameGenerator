from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pg_gen.world.CollisionFlags import CollisionFlags

from ..support.Point import Point
from ..support.support import resolve_intersection
from .SpriteLayer import SpriteLayer

if TYPE_CHECKING:
    from ..game_core.Universe import Universe
    from .World import World


@dataclass(eq=False)
class Actor:
    universe: "Universe" = field(repr=False, default=None)  # type: ignore
    position: Point = Point.ZERO
    size: Point = Point.ONE
    collision_flags: CollisionFlags = field(default=CollisionFlags(0), repr=False)
    world: "World" = field(repr=False, init=False, default=None)  # type: ignore
    layer: SpriteLayer = SpriteLayer.NORMAL

    def draw(self): ...
    def update(self, delta: float): ...
    def on_created(self): ...
    def on_added(self): ...
    def on_removed(self): ...

    def on_trigger(self, trigger: "Actor"): ...

    def resolve_intersection(self, position: Point, size: Point) -> Point:
        return resolve_intersection(position, size, self.position, self.size)

    def transfer_world(self, new_world: "World"):
        if self.world is not None:
            self.world.remove_actor(self)
        new_world.add_actor(self)

    def remove(self):
        if self.world is None:
            return
        self.world.remove_actor(self)
