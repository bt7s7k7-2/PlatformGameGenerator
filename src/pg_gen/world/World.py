from typing import TYPE_CHECKING, Iterable, List

from ..support.Point import Point
from ..support.resolve_intersection import is_intersection, resolve_intersection
from .CollisionFlags import CollisionFlags
from .SpriteLayer import SpriteLayer

if TYPE_CHECKING:
    from ..game_core.Universe import Universe
    from .Actor import Actor


class World:
    active = False
    paused = False

    def get_actors(self) -> Iterable["Actor"]:
        return self._actors

    def add_actor(self, actor: "Actor", in_front=False):
        is_new = actor.universe is None  # type: ignore
        actor.world = self
        actor.universe = self.universe
        if is_new:
            actor.on_created()
        if self.active:
            actor.on_added()

        if in_front:
            self._actors.insert(0, actor)
        else:
            self._actors.append(actor)

        if CollisionFlags.STATIC in actor.collision_flags:
            if in_front:
                self._colliders.insert(0, actor)
            else:
                self._colliders.append(actor)

        if CollisionFlags.TRIGGER in actor.collision_flags:
            if in_front:
                self._triggers.insert(0, actor)
            else:
                self._triggers.append(actor)

    def add_actors(self, *actors: "Actor"):
        for actor in actors:
            self.add_actor(actor)

    def remove_actor(self, actor: "Actor"):
        if not actor in self._actors:
            return

        actor.world = None  # type: ignore

        self._actors.pop(self._actors.index(actor))

        if CollisionFlags.STATIC in actor.collision_flags:
            self._colliders.pop(self._colliders.index(actor))

        if CollisionFlags.TRIGGER in actor.collision_flags:
            self._triggers.pop(self._triggers.index(actor))

        if self.active:
            actor.on_removed()

    def draw(self):
        for actor in self._actors:
            if actor.layer == SpriteLayer.BACKGROUND:
                actor.draw()

        for actor in self._actors:
            if actor.layer == SpriteLayer.NORMAL:
                actor.draw()

        for actor in self._actors:
            if actor.layer == SpriteLayer.GUI:
                actor.draw()

    def update(self, delta: float):
        if self.paused:
            delta = 0

        for actor in self._actors:
            actor.update(delta)

    def check_triggers(self, actor: "Actor"):
        if self.paused:
            return

        for trigger in self._triggers:
            for collider_position, collider_size in trigger.get_colliders():
                if not is_intersection(actor.position, actor.size, collider_position, collider_size):
                    continue

                trigger.on_trigger(actor)
                actor.on_trigger(trigger)

    def resolve_collisions(self, actor: "Actor"):
        resolution_vector = Point.ZERO

        if self.paused:
            return Point.ZERO

        test_position = actor.position

        for collider in self._colliders:
            for collider_position, collider_size in collider.get_colliders():
                collision = resolve_intersection(test_position, actor.size, collider_position, collider_size)
                if collision != Point.ZERO:
                    collider.on_trigger(actor)
                    resolution_vector += collision
                    test_position += collision

        return resolution_vector

    def check_rect(self, position: Point, size: Point):
        for collider in self._colliders:
            for collider_position, collider_size in collider.get_colliders():
                if is_intersection(position, size, collider_position, collider_size):
                    return True

        return False

    def __init__(self, universe: "Universe") -> None:
        self.universe = universe
        self._actors: List["Actor"] = []
        self._triggers: List["Actor"] = []
        self._colliders: List["Actor"] = []
        pass
