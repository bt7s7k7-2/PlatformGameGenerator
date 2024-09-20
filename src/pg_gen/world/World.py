from dataclasses import astuple
from typing import TYPE_CHECKING, List

from pygame import Surface

if TYPE_CHECKING:
    from ..game_core.Universe import Universe
    from .Entity import Entity

from ..support.Color import Color


class World:
    entities: List["Entity"] = []
    background_color = Color.BLACK

    def add_entity(self, entity: "Entity"):
        self.entities.append(entity)

    def remove_entity(self, entity: "Entity"):
        if not entity in self.entities:
            return

        self.entities.pop(self.entities.index(entity))

    def draw(self, surface: Surface):
        surface.fill(astuple(self.background_color))

        for entity in self.entities:
            entity.draw(surface)

    def __init__(self, universe: "Universe") -> None:
        self.universe = universe
        pass
