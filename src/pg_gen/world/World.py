from dataclasses import astuple
from typing import TYPE_CHECKING, List

from pygame import Surface

if TYPE_CHECKING:
    from .Actor import Actor
    from ..game_core.Universe import Universe

from ..support.Color import Color


class World:
    actors: List["Actor"] = []
    background_color = Color.BLACK

    def add_actor(self, actor: "Actor"):
        actor.world = self
        self.actors.append(actor)

    def remove_actor(self, actor: "Actor"):
        if not actor in self.actors:
            return

        actor.world = None

        self.actors.pop(self.actors.index(actor))

    def draw(self, surface: Surface):
        surface.fill(astuple(self.background_color))

        for actor in self.actors:
            actor.draw(surface)

    def __init__(self, universe: "Universe") -> None:
        self.universe = universe
        pass
