from dataclasses import dataclass, field

from pygame import Surface

from ..game_core.ResourceProvider import ResourceProvider
from ..generation.RoomInfo import NO_KEY, RoomInfo
from ..support.constants import CAMERA_SCALE
from ..support.keys import KEY_COLORS
from ..world.Actor import Actor
from ..world.CollisionFlags import CollisionFlags
from .InventoryItem import InventoryItem
from .Player import Player


@dataclass
class Key(Actor):
    collision_flags: CollisionFlags = field(default=CollisionFlags.TRIGGER)
    key_type: int = NO_KEY
    room: "RoomInfo | None" = field(default=None)

    _resource_provider: ResourceProvider | None = field(init=False, repr=False, default=None)

    def draw(self, surface: Surface):
        color = KEY_COLORS[self.key_type - 1]
        self._resource_provider = self._resource_provider or self.universe.di.inject(ResourceProvider)
        sprite = self._resource_provider.key_sprite
        sprite.tinted(color).draw(surface, self.position, CAMERA_SCALE)

    def on_trigger(self, trigger: Actor):
        if not isinstance(trigger, Player):
            return

        key_item = KeyItem(self.universe, key_type=self.key_type)
        if trigger.add_inventory_item(key_item):
            self.universe.queue_task(lambda: self.remove())
            if self.room is not None:
                self.room.provides_key = NO_KEY


@dataclass
class KeyItem(InventoryItem):
    key_type: int = NO_KEY

    _resource_provider: ResourceProvider | None = field(init=False, repr=False, default=None)

    def draw(self, surface: Surface):
        color = KEY_COLORS[self.key_type - 1]
        self._resource_provider = self._resource_provider or self.universe.di.inject(ResourceProvider)
        sprite = self._resource_provider.key_sprite
        sprite.tinted(color).draw(surface, self.position, CAMERA_SCALE)
