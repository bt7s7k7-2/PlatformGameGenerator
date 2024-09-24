from dataclasses import dataclass, field
from math import copysign
from typing import TYPE_CHECKING, List

import pygame
import pygame.freetype
from pygame import Surface

if TYPE_CHECKING:
    from ..world.World import World

from ..game_core.InputState import InputState
from ..game_core.ResourceProvider import ResourceProvider
from ..support.Color import Color
from ..support.constants import AIR_ACCELERATION, AIR_DRAG, CAMERA_SCALE, GRAVITY, GROUND_VELOCITY, JUMP_IMPULSE
from ..support.Point import Point
from ..world.Actor import Actor
from .InventoryItem import InventoryItem


@dataclass
class Player(Actor):
    size: Point = field(default=Point(1, 2))

    _inventory: List[InventoryItem | None] = field(default_factory=lambda: [None] * 5, init=False)

    _input: InputState = field(init=False, repr=False)
    _resource_provider: ResourceProvider | None = field(init=False, repr=False, default=None)

    velocity: Point = Point.ZERO
    _is_grounded: bool = False

    def __post_init__(self):
        self._input = self.universe.di.inject(InputState)
        self.universe.di.register(Player, self)

    def remove(self):
        self.universe.di.unregister(Player, self)
        return super().remove()

    def draw(self, surface: Surface):
        pygame.draw.rect(
            surface,
            color=Color.YELLOW.to_pygame_color(),
            rect=self.position.to_pygame_rect(self.size, CAMERA_SCALE),
        )

    def add_inventory_item(self, item: InventoryItem):
        assert self.world is not None

        if None not in self._inventory:
            # No free slot in inventory
            return False

        free_slot = self._inventory.index(None)
        item.position = Point(free_slot, 0)
        self._inventory[free_slot] = item
        self.world.add_actor(item)

        return True

    def transfer_world(self, new_world: "World"):
        super().transfer_world(new_world)
        for item in self._inventory:
            if item is not None:
                item.transfer_world(new_world)

    def update(self, delta: float):
        assert self.world is not None

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
