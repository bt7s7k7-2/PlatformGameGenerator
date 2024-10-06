from dataclasses import dataclass, field
from typing import override

from ..game_core.Camera import CameraClient
from ..level_editor.ActorRegistry import ActorRegistry
from ..support.Color import Color
from ..world.CollisionFlags import CollisionFlags


@dataclass
class Wall(CameraClient):
    color: Color = Color.WHITE
    collision_flags: CollisionFlags = field(default=CollisionFlags.STATIC)

    @override
    def draw(self):
        self._camera.draw_placeholder(self.position, self.size, self.color)


ActorRegistry.register_actor(Wall)
