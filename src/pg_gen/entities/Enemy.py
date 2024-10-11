from dataclasses import dataclass

from ..support.Direction import Direction
from ..support.Point import Point
from ..world.Actor import Actor
from ..world.CollisionFlags import CollisionFlags
from .Player import Player


@dataclass
class Enemy(Actor):
    collision_flags: CollisionFlags = CollisionFlags.TRIGGER
    direction: Direction = Direction.RIGHT
    speed = 2

    def update(self, delta: float):
        direction_vector = Point.from_direction(self.direction)
        collision_check_size = Point.ONE * 0.1
        collision_check_point = self.position + self.size * 0.5 + direction_vector * self.size * 0.5 - collision_check_size * 0.5
        will_collide = self.world.check_rect(collision_check_point, collision_check_size)
        if will_collide:
            self.direction = self.direction.invert()
            direction_vector = Point.from_direction(self.direction)

        self.position += direction_vector * self.speed * delta

    def on_trigger(self, trigger: Actor):
        if isinstance(trigger, Player):
            trigger.take_damage()
