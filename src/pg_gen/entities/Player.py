from dataclasses import dataclass, field
from math import copysign
from typing import TYPE_CHECKING, Callable, List

import pygame
import pygame.freetype
from pygame import Surface

from ..game_core.InputClient import InputClient
from ..support.support import find_index_by_predicate

if TYPE_CHECKING:
    from ..world.World import World

from ..support.Color import Color
from ..support.constants import AIR_ACCELERATION, AIR_DRAG, CAMERA_SCALE, GRAVITY, GROUND_VELOCITY, JUMP_IMPULSE
from ..support.Point import Point
from .InventoryItem import InventoryItem


@dataclass
class Player(InputClient):
    size: Point = field(default=Point(1, 2))

    _inventory: List[InventoryItem | None] = field(default_factory=lambda: [None] * 5, init=False)

    velocity: Point = Point.ZERO
    _is_grounded: bool = False

    def on_added(self):
        self.universe.di.register(Player, self)

    def on_removed(self):
        self.universe.di.unregister(Player, self)

    def draw(self, surface: Surface):
        pygame.draw.rect(
            surface,
            color=Color.YELLOW.to_pygame_color(),
            rect=self.position.to_pygame_rect(self.size, CAMERA_SCALE),
        )

    def add_inventory_item(self, item: InventoryItem):
        if None not in self._inventory:
            # No free slot in inventory
            return False

        free_slot = self._inventory.index(None)
        item.position = Point(free_slot, 0)
        self._inventory[free_slot] = item
        self.world.add_actor(item)

        return True

    def take_inventory_item(self, item_predicate: Callable[[InventoryItem | None], bool]):
        item_index = find_index_by_predicate(self._inventory, item_predicate)
        if item_index == -1:
            return None

        item = self._inventory[item_index]
        assert item is not None
        self._inventory[item_index] = None

        item.remove()
        return item

    def transfer_world(self, new_world: "World"):
        super().transfer_world(new_world)
        for item in self._inventory:
            if item is not None:
                item.transfer_world(new_world)

    def update(self, delta: float):
        if self._is_grounded:
            move_vector = Point.ZERO

            if self._input.left:
                move_vector += Point.LEFT

            if self._input.right:
                move_vector += Point.RIGHT

            self.velocity = move_vector * GROUND_VELOCITY + Point.DOWN * 0.01

            if self._input.jump:
                self.velocity += Point.UP * JUMP_IMPULSE
        else:
            drag = self.velocity.right().normalize() * -AIR_DRAG * delta
            if drag.magnitude() > abs(self.velocity.x):
                drag = drag.normalize() * abs(self.velocity.x)
            self.velocity += drag

            self.velocity += Point.DOWN * (GRAVITY * delta)

            if self._input.left:
                self.velocity += Point.LEFT * delta * AIR_ACCELERATION

            if self._input.right:
                self.velocity += Point.RIGHT * delta * AIR_ACCELERATION

            if abs(self.velocity.x) > GROUND_VELOCITY:
                self.velocity = Point(copysign(GROUND_VELOCITY, self.velocity.x), self.velocity.y)

        self.position += self.velocity * delta
        collision_resolution = self.world.resolve_collisions(self)
        self.position += collision_resolution

        # Make sure that if the ceiling is hit we reset the vertical velocity
        if collision_resolution.y > 0 and self.velocity.y < 0:
            self.velocity = self.velocity * Point.RIGHT

        self._is_grounded = collision_resolution.y < 0

        self.world.check_triggers(self)
