from dataclasses import dataclass, field
from enum import Flag
from math import copysign
from typing import TYPE_CHECKING, Callable, List

import pygame

from ..game_core.InputClient import InputClient
from ..support.Color import Color
from ..support.support import find_index_by_predicate
from .support.GuiRenderer import GuiRenderer
from .support.SpriteActor import SpriteActor

if TYPE_CHECKING:
    from .progression.Climbable import Climbable
    from ..world.World import World

from ..support.constants import AIR_ACCELERATION, AIR_DRAG, CLIMB_VELOCITY, GRAVITY, GROUND_VELOCITY, JUMP_IMPULSE, SLIDE_VELOCITY, TEXT_COLOR
from ..support.Point import Point
from .support.InventoryItem import InventoryItem


class ClimbState(Flag):
    READY = 1
    CLIMBING = 2
    SLIDING = 4


@dataclass
class Player(InputClient, GuiRenderer, SpriteActor):
    size: Point = field(default=Point(1, 1))
    sprite: str = field(default="player_sprite")

    _inventory: List[InventoryItem | None] = field(default_factory=lambda: [None] * 5, init=False)

    velocity: Point = Point.ZERO
    _is_grounded: bool = False
    _did_jump: bool = False
    _spawn_point: Point = Point.ZERO
    _spawn_state: ClimbState = ClimbState(0)

    curr_climbable: "Climbable | None" = None
    climb_state: ClimbState = ClimbState(0)
    score = 0

    def respawn(self):
        self.position = self._spawn_point
        self.climb_state = self._spawn_state

    def take_damage(self):
        self.universe.queue_task(self.respawn)

    def on_added(self):
        self._spawn_point = self.position
        self._spawn_state = self.climb_state
        self.universe.di.register(Player, self)

    def on_removed(self):
        self.universe.di.unregister(Player, self)

    def draw_gui(self):
        text = str(self.score).zfill(6)
        position = self._camera.world_to_screen(Point(11, 0.25))
        text_buffer, _ = self._resource_provider.display_font.render(text=text, fgcolor=TEXT_COLOR)
        text_size = Point(*text_buffer.get_size())
        gradient_splits = 5
        for y in range(gradient_splits):
            color = Color.RED.mix(Color.YELLOW, 0.25 + (y / gradient_splits) * 0.5)
            text_buffer.fill(color.to_pygame_color(), (text_size.down() * y / gradient_splits).to_pygame_rect(text_size * Point(1, 1 / gradient_splits)), pygame.BLEND_RGB_MULT)

        self._camera.screen.blit(text_buffer, position.to_pygame_coordinates())

        return super().draw_gui()

    def add_inventory_item(self, item: InventoryItem):
        if None not in self._inventory:
            # No free slot in inventory
            return False

        free_slot = self._inventory.index(None)
        item.position = Point(free_slot, 0)
        self._inventory[free_slot] = item
        self.world.add_actor(item)
        self.score += 10

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
        self.curr_climbable = None

    def update(self, delta: float):
        if self.world.paused:
            return

        self.world.check_triggers(self)

        should_jump = self._input.jump and not self._did_jump
        self._did_jump = self._input.jump

        if self.climb_state & ClimbState.CLIMBING:
            if self.curr_climbable is None:
                self.climb_state = ClimbState(0)
            else:
                if should_jump:
                    self.climb_state = ClimbState(0)
                    self.curr_climbable = None
                    self._is_grounded = False
                    self.velocity = Point.UP * JUMP_IMPULSE

                    if self._input.left:
                        self.velocity += Point.LEFT * GROUND_VELOCITY

                    if self._input.right:
                        self.velocity += Point.RIGHT * GROUND_VELOCITY
                else:

                    # Only allow climbing up if we are not on a slide only climbable
                    if self.climb_state & ClimbState.SLIDING:
                        if self._input.down:
                            self.position += Point.DOWN * SLIDE_VELOCITY * delta
                    else:
                        if self._input.up:
                            self.position += Point.UP * CLIMB_VELOCITY * delta

                        if self._input.down:
                            self.position += Point.DOWN * CLIMB_VELOCITY * delta
                            max_y = self.curr_climbable.position.y + self.curr_climbable.size.y - 1
                            if self.position.y > max_y:
                                self.position = Point(self.position.x, max_y)

                    if self._input.left:
                        self.flip = False

                    if self._input.right:
                        self.flip = True

                    self.curr_climbable = None
                    # If we are climbing, do skip further input and physics processing
                    return

        if self.curr_climbable is not None and self.climb_state == ClimbState(0) and should_jump:
            self.climb_state = ClimbState.CLIMBING
            self._is_grounded = False
            if self.curr_climbable.slide_only:
                self.climb_state |= ClimbState.SLIDING

            # Force X position to be center of the climbable
            self.position = self.position.down() + self.curr_climbable.position.right()
            return
        elif self._is_grounded:
            move_vector = Point.ZERO

            if self._input.left:
                move_vector += Point.LEFT
                self.flip = False

            if self._input.right:
                move_vector += Point.RIGHT
                self.flip = True

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
                self.flip = False

            if self._input.right:
                self.velocity += Point.RIGHT * delta * AIR_ACCELERATION
                self.flip = True

            if abs(self.velocity.x) > GROUND_VELOCITY:
                self.velocity = Point(copysign(GROUND_VELOCITY, self.velocity.x), self.velocity.y)

        self.position += self.velocity * delta
        collision_resolution = self.world.resolve_collisions(self)
        self.position += collision_resolution

        # Make sure that if the ceiling is hit we reset the vertical velocity
        if collision_resolution.y > 0 and self.velocity.y < 0:
            self.velocity = self.velocity * Point.RIGHT

        self._is_grounded = collision_resolution.y < 0
        self.curr_climbable = None
