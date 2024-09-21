from dataclasses import astuple
from typing import TYPE_CHECKING, List

from pygame import Surface

from ..support.Point import Point
from ..support.support import is_intersection, resolve_intersection
from .CollisionFlags import CollisionFlags

if TYPE_CHECKING:
    from .Actor import Actor
    from ..game_core.Universe import Universe

from ..support.Color import Color


class World:
    background_color = Color.BLACK

    def add_actor(self, actor: "Actor"):
        actor.world = self
        self._actors.append(actor)

        if CollisionFlags.STATIC in actor.collision_flags:
            self._colliders.append(actor)

        if CollisionFlags.TRIGGER in actor.collision_flags:
            self._triggers.append(actor)

    def remove_actor(self, actor: "Actor"):
        if not actor in self._actors:
            return

        actor.world = None

        self._actors.pop(self._actors.index(actor))

        if CollisionFlags.STATIC in actor.collision_flags:
            self._colliders.pop(self._colliders.index(actor))

        if CollisionFlags.TRIGGER in actor.collision_flags:
            self._triggers.pop(self._triggers.index(actor))

    def draw(self, surface: Surface):
        surface.fill(astuple(self.background_color))

        for actor in self._actors:
            actor.draw(surface)

    def update(self, delta: float):
        for actor in self._actors:
            actor.update(delta)

    def check_triggers(self, actor: "Actor"):
        for trigger in self._triggers:
            if not is_intersection(actor.position, actor.size, trigger.position, trigger.size):
                continue

            trigger.on_trigger(actor)
            actor.on_trigger(trigger)

    def resolve_collisions(self, actor: "Actor"):
        resolution_vector = Point.ZERO

        for collider in self._colliders:
            resolution_vector += resolve_intersection(actor.position, actor.size, collider.position, collider.size)

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
