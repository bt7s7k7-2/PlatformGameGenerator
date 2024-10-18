from dataclasses import dataclass, field

from ...game_core.Camera import CameraClient
from ...game_core.ResourceClient import ResourceClient
from ...generation.RoomInfo import NO_KEY, RoomInfo
from ...level_editor.ActorRegistry import ActorRegistry
from ...support.keys import KEY_COLORS, MAX_KEY_TYPE
from ...world.Actor import Actor
from ...world.CollisionFlags import CollisionFlags
from ..Player import Player
from ..support.InventoryItem import InventoryItem


@dataclass
class Key(ResourceClient, CameraClient):
    collision_flags: CollisionFlags = field(default=CollisionFlags.TRIGGER)
    key_type: int = NO_KEY
    room: "RoomInfo | None" = field(default=None)

    def draw(self):
        color = KEY_COLORS[self.key_type - 1]
        sprite = self._resource_provider.key_sprite
        self._camera.draw_texture(self.position, self.size, sprite, color)

    def on_trigger(self, trigger: Actor):
        if not isinstance(trigger, Player):
            return

        key_item = KeyItem(key_type=self.key_type)
        if trigger.add_inventory_item(key_item):
            self.universe.queue_task(lambda: self.remove())
            if self.room is not None:
                self.room.provides_key = NO_KEY


@dataclass
class KeyItem(InventoryItem, ResourceClient, CameraClient):
    key_type: int = NO_KEY

    def draw(self):
        color = KEY_COLORS[self.key_type - 1]
        sprite = self._resource_provider.key_sprite
        self._camera.draw_texture(self.position, self.size, sprite, color)
