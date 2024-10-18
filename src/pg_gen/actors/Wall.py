from dataclasses import dataclass, field
from typing import override

from ..game_core.Camera import CameraClient
from ..game_core.ResourceClient import ResourceClient
from ..level_editor.ActorRegistry import ActorRegistry
from ..support.Point import Point
from ..world.CollisionFlags import CollisionFlags
from ..world.SpriteLayer import SpriteLayer


@dataclass
class Wall(CameraClient, ResourceClient):
    collision_flags: CollisionFlags = field(default=CollisionFlags.STATIC)
    layer: SpriteLayer = field(default=SpriteLayer.BACKGROUND)

    @override
    def draw(self):
        self._camera.draw_texture(self.position, Point.ONE, self._resource_provider.wall_sprite, repeat=self.size)


@dataclass
class WallSlope(CameraClient, ResourceClient):
    collision_flags: CollisionFlags = field(default=CollisionFlags.STATIC)
    layer: SpriteLayer = field(default=SpriteLayer.BACKGROUND)

    horizontal: bool = False
    invert: bool = False
    reverse: bool = False

    @override
    def get_colliders(self):
        start = self.position
        extend = (self.size).dominant_size() * 2

        main_axis = Point.DOWN if not self.horizontal else Point.RIGHT
        cross_axis = Point.RIGHT if not self.horizontal else Point.DOWN

        segment_size_cross = self.size * cross_axis
        segment_size_main = main_axis * 0.5

        for i in range(int(extend)):
            position = start + main_axis * (0.5 * i)

            t = (i + 1) / extend if not self.invert else (extend - i) / extend
            size = segment_size_cross * t + segment_size_main

            if self.reverse:
                position += self.size * cross_axis - segment_size_cross * t

            yield position, size

    @override
    def draw(self):
        for position, size in self.get_colliders():
            self._camera.draw_texture(position, Point.ONE, self._resource_provider.wall_sprite, repeat=size)


ActorRegistry.register_actor(Wall)
ActorRegistry.register_actor(WallSlope, name_override="Slope\\#", default_value=WallSlope(horizontal=True, invert=False))
ActorRegistry.register_actor(WallSlope, name_override="Slope#/", default_value=WallSlope(horizontal=True, invert=True))
ActorRegistry.register_actor(WallSlope, name_override="Slope/#", default_value=WallSlope(horizontal=False, invert=False, reverse=True))
ActorRegistry.register_actor(WallSlope, name_override="Slope#\\", default_value=WallSlope(horizontal=False, invert=False))
