from dataclasses import dataclass, field
from typing import override

from ..game_core.Camera import CameraClient
from ..game_core.ResourceClient import ResourceClient
from ..level_editor.ActorRegistry import ActorRegistry
from ..support.Color import Color
from ..support.Point import Point
from ..world.CollisionFlags import CollisionFlags


@dataclass
class Wall(CameraClient, ResourceClient):
    color: Color = Color.WHITE
    collision_flags: CollisionFlags = field(default=CollisionFlags.STATIC)

    @override
    def draw(self):
        self._camera.draw_placeholder(self.position, self.size, self.color)
        self._camera.draw_texture(self.position, Point.ONE, self._resource_provider.wall_sprite, repeat=self.size)


ActorRegistry.register_actor(Wall)
