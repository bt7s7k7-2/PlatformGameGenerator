from dataclasses import dataclass, field
from typing import override

from ...level_editor.ActorRegistry import ActorRegistry
from ...support.Direction import Direction
from ...support.Point import Point
from ..support.SpriteActor import SpriteActor
from .Enemy import Enemy


@dataclass
class RollingSkull(Enemy, SpriteActor):
    sprite: str = field(default="skull_sprite")

    @override
    def get_colliders(self):
        yield self.position + self.size * Point(0.375, 0.75), self.size * 0.25

    def update(self, delta: float):
        rotation_speed = self.speed * 100
        self.rotation += delta * rotation_speed if self.direction == Direction.LEFT else -delta * rotation_speed
        return super().update(delta)


ActorRegistry.register_actor(RollingSkull, name_override="Skull:roll")
