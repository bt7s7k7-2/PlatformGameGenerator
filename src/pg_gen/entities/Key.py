from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pygame
from pygame import Surface

if TYPE_CHECKING:
    from ..generation.MapGenerator import RoomInfo

from ..support.constants import CAMERA_SCALE
from ..support.keys import KEY_COLORS
from ..world.Actor import Actor
from ..world.CollisionFlags import CollisionFlags
from .InventoryItem import InventoryItem
from .Player import Player


@dataclass
class Key(Actor):
    collision_flags: CollisionFlags = field(default=CollisionFlags.TRIGGER)
    key_type: int = 0
    room: "RoomInfo | None" = field(default=None)

    def draw(self, surface: Surface):
        color = KEY_COLORS[self.key_type]
        pygame.draw.rect(surface, color.to_pygame_color(), self.position.to_pygame_rect(self.size, CAMERA_SCALE))

    def on_trigger(self, trigger: Actor):
        if not isinstance(trigger, Player):
            return

        key_item = KeyItem(self.universe, key_type=self.key_type)
        if trigger.add_inventory_item(key_item):
            self.universe.queue_task(lambda: self.remove())
            if self.room is not None:
                self.room.provides_key = -1


@dataclass
class KeyItem(InventoryItem):
    key_type: int = 0

    def draw(self, surface: Surface):
        color = KEY_COLORS[self.key_type]
        pygame.draw.rect(surface, color.to_pygame_color(), self.position.to_pygame_rect(self.size, CAMERA_SCALE))
