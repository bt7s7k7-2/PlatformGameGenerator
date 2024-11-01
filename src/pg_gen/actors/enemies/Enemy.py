from dataclasses import dataclass
from typing import override

from ...support.Direction import Direction
from ...support.Point import Point
from ...world.Actor import Actor
from ...world.CollisionFlags import CollisionFlags
from ..Player import Player


@dataclass
class Enemy(Actor):
    collision_flags: CollisionFlags = CollisionFlags.TRIGGER
    direction: Direction = Direction.RIGHT
    speed: float = 2
    collider_size: float = 1
    can_fall: bool = True

    @override
    def get_colliders(self):
        yield self.position + self.size * Point(0.5 - self.collider_size * 0.5, 1 - self.collider_size), self.size * self.collider_size

    def update(self, delta: float):
        direction_vector = Point.from_direction(self.direction)
        collision_check_size = Point.ONE * 0.1

        def check(vector: Point):
            collision_check_point = self.position + self.size * 0.5 + vector * self.size * 0.5 - collision_check_size * 0.5
            return self.world.check_rect(collision_check_point, collision_check_size)

        will_collide = check(direction_vector)
        will_fall = self.can_fall and not check(direction_vector * 0.5 + Point.DOWN)

        if will_collide or will_fall:
            self.direction = self.direction.invert()
            direction_vector = Point.from_direction(self.direction)

        self.position += direction_vector * self.speed * delta

    def on_trigger(self, trigger: Actor):
        if isinstance(trigger, Player):
            trigger.take_damage()
