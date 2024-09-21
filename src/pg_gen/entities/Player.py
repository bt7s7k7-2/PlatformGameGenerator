from dataclasses import dataclass, field
from math import copysign

import pygame
import pygame.freetype
from pygame import Surface

from ..game_core.InputState import InputState
from ..game_core.ResourceProvider import ResourceProvider
from ..support.Color import Color
from ..support.constants import AIR_ACCELERATION, CAMERA_SCALE, GRAVITY, GROUND_VELOCITY, JUMP_IMPULSE
from ..support.Point import Point
from ..world.Actor import Actor


@dataclass
class Player(Actor):
    size: Point = field(default=Point(1, 2))

    _input: InputState = field(init=False, repr=False)
    _resource_provider: ResourceProvider | None = field(init=False, repr=False, default=None)

    _velocity: Point = Point.ZERO
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

    def update(self, delta: float):
        assert self.world is not None

        if self._is_grounded:
            move_vector = Point.ZERO

            if self._input.left:
                move_vector += Point.LEFT

            if self._input.right:
                move_vector += Point.RIGHT

            self._velocity = move_vector * GROUND_VELOCITY + Point.DOWN * 0.01

            if self._input.jump:
                self._velocity += Point.UP * JUMP_IMPULSE
        else:
            self._velocity += Point.DOWN * (GRAVITY * delta)

            if self._input.left:
                self._velocity += Point.LEFT * delta * AIR_ACCELERATION

            if self._input.right:
                self._velocity += Point.RIGHT * delta * AIR_ACCELERATION

            if abs(self._velocity.x) > GROUND_VELOCITY:
                self._velocity = Point(copysign(GROUND_VELOCITY, self._velocity.x), self._velocity.y)

        self.position += self._velocity * delta
        collision_resolution = self.world.resolve_collisions(self)
        self.position += collision_resolution

        # Make sure that if the ceiling is hit we reset the vertical velocity
        if collision_resolution.y > 0 and self._velocity.y < 0:
            self._velocity = self._velocity * Point.RIGHT

        self._is_grounded = collision_resolution.y < 0
