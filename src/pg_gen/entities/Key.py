from dataclasses import dataclass, field

from pygame import Surface

from ..game_core.ResourceClient import ResourceClient
from ..generation.RoomInfo import NO_KEY, RoomInfo
from ..level_editor.ActorRegistry import ActorRegistry
from ..support.constants import CAMERA_SCALE
from ..support.keys import KEY_COLORS, MAX_KEY_TYPE
from ..world.Actor import Actor
from ..world.CollisionFlags import CollisionFlags
from .InventoryItem import InventoryItem
from .Player import Player


@dataclass
class Key(ResourceClient):
    collision_flags: CollisionFlags = field(default=CollisionFlags.TRIGGER)
    key_type: int = NO_KEY
    room: "RoomInfo | None" = field(default=None)

    def draw(self, surface: Surface):
        color = KEY_COLORS[self.key_type - 1]
        sprite = self._resource_provider.key_sprite
        sprite.tinted(color).draw(surface, self.position, CAMERA_SCALE)

    def on_trigger(self, trigger: Actor):
        if not isinstance(trigger, Player):
            return

        key_item = KeyItem(key_type=self.key_type)
        if trigger.add_inventory_item(key_item):
            self.universe.queue_task(lambda: self.remove())
            if self.room is not None:
                self.room.provides_key = NO_KEY


for key_type in range(MAX_KEY_TYPE):
    ActorRegistry.register_actor(Key, suffix=str(key_type + 1), default_value=Key(key_type=key_type + 1))


@dataclass
class KeyItem(InventoryItem, ResourceClient):
    key_type: int = NO_KEY

    def draw(self, surface: Surface):
        color = KEY_COLORS[self.key_type - 1]
        sprite = self._resource_provider.key_sprite
        sprite.tinted(color).draw(surface, self.position, CAMERA_SCALE)
