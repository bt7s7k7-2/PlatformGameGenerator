from dataclasses import dataclass, field
from typing import override

from ...game_core.Camera import CameraClient
from ...game_core.ResourceClient import ResourceClient
from ...support.Point import Point
from ...world.Actor import Actor
from ...world.CollisionFlags import CollisionFlags
from ..Player import Player


@dataclass
class Climbable(CameraClient, ResourceClient):
    collision_flags: CollisionFlags = field(default=CollisionFlags.TRIGGER)
    sprite: str = ""
    slide_only: bool = False

    @override
    def draw(self):
        self._camera.draw_texture(self.position, Point.ONE, self._resource_provider.__getattribute__(self.sprite), repeat=self.size)

    def on_trigger(self, trigger: Actor):
        if isinstance(trigger, Player):
            trigger.curr_climbable = self
        return super().on_trigger(trigger)
