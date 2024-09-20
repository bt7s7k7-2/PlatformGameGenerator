from dataclasses import dataclass
from enum import Enum

from ..support.Point import Point
from .Entity import Entity


class CollisionType(Enum):
    NONE = 0
    PLAYER = 1
    STATIC = 2
    TRIGGER = 3


@dataclass
class Actor(Entity):
    position: Point
    size: Point
    collision_type: CollisionType = CollisionType.NONE

    def on_collision(self, collision_object: "Actor"): ...
    def on_trigger(self, trigger: "Actor"): ...
