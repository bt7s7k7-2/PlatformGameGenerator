from dataclasses import dataclass, field
from typing import override

from ...difficulty.DifficultyProvider import DifficultyProvider
from ...difficulty.DifficultyReport import DifficultyReport
from ...game_core.Camera import CameraClient
from ...game_core.ResourceClient import ResourceClient
from ...generation.RoomInfo import ALTAR, NO_KEY, RoomInfo
from ...generation.RoomParameter import RoomParameter
from ...level_editor.ActorRegistry import ActorRegistry
from ...support.keys import KEY_COLORS
from ...world.Actor import Actor
from ...world.CollisionFlags import CollisionFlags
from ..Player import Player
from ..support.InventoryItem import InventoryItem


@dataclass
class Key(ResourceClient, CameraClient, DifficultyProvider):
    collision_flags: CollisionFlags = field(default=CollisionFlags.TRIGGER)
    key_type: int = NO_KEY
    room: "RoomInfo | None" = field(default=None)

    @override
    def draw(self):
        if self.key_type == ALTAR:
            self._camera.draw_texture(self.position, self.size, self._resource_provider.eye_sprite)
            return

        color = KEY_COLORS[self.key_type - 1]
        sprite = self._resource_provider.key_sprite
        self._camera.draw_texture(self.position, self.size, sprite, color)

    @override
    def on_trigger(self, trigger: Actor):
        if not isinstance(trigger, Player):
            return

        key_item = KeyItem(key_type=self.key_type)
        if trigger.add_inventory_item(key_item):
            self.universe.queue_task(lambda: self.remove())
            if self.room is not None:
                self.room.pickup_type = NO_KEY

    @override
    def apply_difficulty(self, difficulty: DifficultyReport):
        difficulty.increment_parameter(RoomParameter.REWARD, 10)


ActorRegistry.register_actor(Key, name_override="Eye", default_value=Key(key_type=ALTAR))


@dataclass
class KeyItem(InventoryItem, ResourceClient, CameraClient):
    key_type: int = NO_KEY

    @override
    def draw(self):
        if self.key_type == ALTAR:
            self._camera.draw_texture(self.position, self.size, self._resource_provider.eye_sprite)
            return

        color = KEY_COLORS[self.key_type - 1]
        sprite = self._resource_provider.key_sprite
        self._camera.draw_texture(self.position, self.size, sprite, color)
