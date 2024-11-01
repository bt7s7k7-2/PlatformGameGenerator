from dataclasses import dataclass, field
from math import sin

from ...level_editor.ActorRegistry import ActorRegistry
from ...support.Direction import Direction
from ...support.Point import Point
from ..support.SpriteActor import SpriteActor
from .Enemy import Enemy


@dataclass
class RollingEnemy(Enemy, SpriteActor):
    def update(self, delta: float):
        rotation_speed = self.speed * 100
        self.rotation += delta * rotation_speed if self.direction == Direction.LEFT else -delta * rotation_speed
        return super().update(delta)


@dataclass
class FloatingEnemy(Enemy, SpriteActor):
    time = 0.0
    can_fall: bool = field(default=False)

    def update(self, delta: float):
        last_offset = sin(self.time)
        self.time += delta * self.speed * 2
        offset = sin(self.time)
        offset_delta = offset - last_offset
        self.position += Point.DOWN * offset_delta * 0.5
        super().update(delta)
        self.flip = self.direction == Direction.RIGHT


ActorRegistry.register_actor(RollingEnemy, name_override="Skull:roll", default_value=RollingEnemy(sprite="skull_sprite", collider_size=0.25))
ActorRegistry.register_actor(FloatingEnemy, name_override="Bobber", default_value=FloatingEnemy(sprite="bobber_sprite", collider_size=0.25, speed=3))
