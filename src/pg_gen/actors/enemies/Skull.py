from dataclasses import dataclass, field

from ...level_editor.ActorRegistry import ActorRegistry
from ...support.Direction import Direction
from ..support.SpriteActor import SpriteActor
from .Enemy import Enemy


@dataclass
class RollingSkull(Enemy, SpriteActor):
    sprite: str = field(default="skull_sprite")

    def update(self, delta: float):
        rotation_speed = self.speed * 100
        self.rotation += delta * rotation_speed if self.direction == Direction.LEFT else -delta * rotation_speed
        return super().update(delta)


ActorRegistry.register_actor(RollingSkull, name_override="Skull:roll")
