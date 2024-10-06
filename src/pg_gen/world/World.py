from dataclasses import astuple
from typing import TYPE_CHECKING, Iterable, List

from pygame import Surface

from ..support.Point import Point
from ..support.support import is_intersection, resolve_intersection
from .CollisionFlags import CollisionFlags
from .SpriteLayer import SpriteLayer

if TYPE_CHECKING:
    from .Actor import Actor
    from ..game_core.Universe import Universe

from ..support.Color import Color


class World:
    background_color = Color.BLACK

    def get_actors(self) -> Iterable["Actor"]:
        return self._actors

    def add_actor(self, actor: "Actor"):
        actor.world = self
        actor.universe = self.universe
        actor.on_added()

        self._actors.append(actor)

        if CollisionFlags.STATIC in actor.collision_flags:
            self._colliders.append(actor)

        if CollisionFlags.TRIGGER in actor.collision_flags:
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

        actor.on_removed()

    def draw(self, surface: Surface):
        surface.fill(astuple(self.background_color))

        for actor in self._actors:
            if actor.layer == SpriteLayer.BACKGROUND:
                actor.draw(surface)

        for actor in self._actors:
            if actor.layer == SpriteLayer.NORMAL:
                actor.draw(surface)

        for actor in self._actors:
            if actor.layer == SpriteLayer.GUI:
                actor.draw(surface)

    def update(self, delta: float):
        if self.universe.paused:
            delta = 0

        for actor in self._actors:
            actor.update(delta)

    def check_triggers(self, actor: "Actor"):
        if self.universe.paused:
            return

        for trigger in self._triggers:
            if not is_intersection(actor.position, actor.size, trigger.position, trigger.size):
                continue

            trigger.on_trigger(actor)
            actor.on_trigger(trigger)

    def resolve_collisions(self, actor: "Actor"):
        resolution_vector = Point.ZERO

        if self.universe.paused:
            return Point.ZERO

        test_position = actor.position

        for collider in self._colliders:
            collision = resolve_intersection(test_position, actor.size, collider.position, collider.size)
            if collision != Point.ZERO:
                collider.on_trigger(actor)
                resolution_vector += collision
                test_position += collision

        return resolution_vector

    def check_rect(self, position: Point, size: Point):
        for collider in self._colliders:
            if is_intersection(position, size, collider.position, collider.size):
                return True

        return False

    def __init__(self, universe: "Universe") -> None:
        self.universe = universe
        self._actors: List["Actor"] = []
        self._triggers: List["Actor"] = []
        self._colliders: List["Actor"] = []
        pass
