from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...game_core.Camera import CameraClient
from ...game_core.ResourceClient import ResourceClient
from ...generation.RoomInfo import NO_KEY
from ...support.keys import KEY_COLORS
from ...support.Point import Point
from ...world.Actor import Actor
from ...world.CollisionFlags import CollisionFlags
from ...world.SpriteLayer import SpriteLayer
from ..Player import Player
from ..support.PersistentObject import PersistentObject
from .Key import KeyItem


class DoorState(Enum):
    CLOSED = 0
    OPEN_LEFT = 1
    OPEN_RIGHT = 2


@dataclass
class Door(ResourceClient, CameraClient, PersistentObject[DoorState]):
    collision_flags: CollisionFlags = field(default=CollisionFlags.STATIC)
    key_type: int = NO_KEY
    size: Point = field(default=Point(1, 2))
    layer: SpriteLayer = field(default=SpriteLayer.BACKGROUND)
    state: DoorState = DoorState.CLOSED

    def _get_default_persistent_value(self) -> Any:
        return DoorState.CLOSED

    def on_created(self):
        self.state = self.persistent_value
        if self.state != DoorState.CLOSED:
            self.collision_flags = CollisionFlags(0)

    def draw(self):
        color = KEY_COLORS[self.key_type - 1]

        if self.state == DoorState.CLOSED:
            margin = 0.1
            self._camera.draw_placeholder(self.position + Point(margin, 0), self.size - Point(margin * 2, 0), color)
        else:
            color = color * 0.75
            position = self.position

            sprite = self._resource_provider.door_sprite

            if self.state == DoorState.OPEN_LEFT:
                position -= Point(1, 0)

            self._camera.draw_texture(position, Point(2, 2), sprite, color)

    def on_trigger(self, trigger: Actor):
        if not isinstance(trigger, Player):
            return

        player_had_key = trigger.take_inventory_item(lambda v: isinstance(v, KeyItem) and v.key_type == self.key_type) is not None
        if player_had_key:
            opened_from_left = self.position.x > trigger.position.x

            self.state = DoorState.OPEN_RIGHT if opened_from_left else DoorState.OPEN_LEFT
            self.persistent_value = self.state

            # Remove and insert ourselves from the world so our collision flags get updated
            world = self.world
            world.remove_actor(self)
            self.collision_flags = CollisionFlags(0)
            world.add_actor(self)
