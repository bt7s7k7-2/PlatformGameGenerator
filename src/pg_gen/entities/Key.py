from dataclasses import dataclass, field

import pygame
from pygame import Surface

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

    def draw(self, surface: Surface):
        color = KEY_COLORS[self.key_type - 1]
        pygame.draw.rect(surface, color.to_pygame_color(), self.position.to_pygame_rect(self.size, CAMERA_SCALE))

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

    def draw(self, surface: Surface):
        color = KEY_COLORS[self.key_type - 1]
        pygame.draw.rect(surface, color.to_pygame_color(), self.position.to_pygame_rect(self.size, CAMERA_SCALE))
