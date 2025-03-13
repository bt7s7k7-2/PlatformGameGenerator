from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, override

from ..game_core.Camera import Camera, CameraClient
from ..game_core.ResourceClient import ResourceClient
from ..generation.RoomInfo import NO_KEY, NOT_CONNECTED
from ..level_editor.ActorRegistry import ActorRegistry
from ..support.Color import Color
from ..support.Direction import Direction
from ..support.Point import Point
from ..world.Actor import Actor
from ..world.CollisionFlags import CollisionFlags
from ..world.SpriteLayer import SpriteLayer
from .progression.Door import Door
from .progression.Key import Key
from .Wall import Wall

if TYPE_CHECKING:
    from ..generation.RoomInstantiationContext import RoomInstantiationContext


def _draw_direction(camera: Camera, position: Point, size: Point, direction: Direction):
    center = position + size * 0.5
    vector = Point.from_direction(direction) * 0.1
    camera.draw_placeholder(center - vector, Point.ONE * 0.1, Color.WHITE)
    camera.draw_placeholder(center + vector, Point.ONE * 0.1, Color.RED)


class Placeholder(Actor):
    _flip: bool = False

    @override
    def flip_x(self):
        self._flip = not self._flip
        return super().flip_x()

    def evaluate_placeholder(self, context: "RoomInstantiationContext") -> Actor | Literal[False]: ...


@dataclass
class DoorPlaceholder(CameraClient, Placeholder):
    size: Point = field(default=Point(1, 2))
    direction: Direction = Direction.LEFT

    @override
    def evaluate_placeholder(self, context: "RoomInstantiationContext"):
        door_type = context.room.get_connection(self.direction.flipX(self._flip))
        if door_type > NO_KEY:
            return Door(
                position=self.position,
                key_type=door_type,
                room=context.room,
            )

        return False

    @override
    def draw(self):
        self._camera.draw_placeholder(self.position, self.size, Color.YELLOW * 0.75)
        _draw_direction(self._camera, self.position, self.size, self.direction)
        return super().draw()


ActorRegistry.register_actor(DoorPlaceholder, name_override="Door:left", default_value=DoorPlaceholder(direction=Direction.LEFT))
ActorRegistry.register_actor(DoorPlaceholder, name_override="Door:right", default_value=DoorPlaceholder(direction=Direction.RIGHT))
ActorRegistry.register_actor(DoorPlaceholder, name_override="Door:up", default_value=DoorPlaceholder(direction=Direction.UP))
ActorRegistry.register_actor(DoorPlaceholder, name_override="Door:down", default_value=DoorPlaceholder(direction=Direction.DOWN))


@dataclass
class KeyPlaceholder(CameraClient, ResourceClient, Placeholder):
    @override
    def draw(self):
        self._camera.draw_texture(self.position, self.size, self._resource_provider.key_sprite, Color.YELLOW)
        return super().draw()

    @override
    def evaluate_placeholder(self, context: "RoomInstantiationContext"):
        door_type = context.room.provides_key
        if door_type != NO_KEY:
            return Key(position=self.position, key_type=door_type, room=context.room)
        return False


ActorRegistry.register_actor(KeyPlaceholder, name_override="Key")


@dataclass
class WallPlaceholder(CameraClient, ResourceClient, Placeholder):
    direction: Direction = Direction.LEFT
    collision_flags: CollisionFlags = field(default=CollisionFlags.STATIC)
    layer: SpriteLayer = field(default=SpriteLayer.BACKGROUND)

    @override
    def evaluate_placeholder(self, context: "RoomInstantiationContext"):
        door_type = context.room.get_connection(self.direction.flipX(self._flip))
        if door_type == NOT_CONNECTED:
            return Wall(position=self.position, size=self.size)
        return False

    @override
    def draw(self):
        self._camera.draw_texture(self.position, Point.ONE, self._resource_provider.wall_sprite, Color.YELLOW, repeat=self.size)
        _draw_direction(self._camera, self.position, self.size, self.direction)


ActorRegistry.register_actor(WallPlaceholder, name_override="Wall:left", default_value=WallPlaceholder(direction=Direction.LEFT))
ActorRegistry.register_actor(WallPlaceholder, name_override="Wall:right", default_value=WallPlaceholder(direction=Direction.RIGHT))
ActorRegistry.register_actor(WallPlaceholder, name_override="Wall:up", default_value=WallPlaceholder(direction=Direction.UP))
ActorRegistry.register_actor(WallPlaceholder, name_override="Wall:down", default_value=WallPlaceholder(direction=Direction.DOWN))
