from dataclasses import dataclass, field
from typing import override

from ...game_core.Camera import CameraClient
from ...game_core.ResourceClient import ResourceClient
from ...level_editor.ActorRegistry import ActorRegistry
from ...support.Point import Point
from ...world.Actor import Actor
from ...world.CollisionFlags import CollisionFlags
from ..Player import Player


@dataclass
class Fire(ResourceClient, CameraClient):
    collision_flags: CollisionFlags = field(default=CollisionFlags.TRIGGER)
    time = 0.0

    @override
    def update(self, delta: float):
        self.time += delta
        return super().update(delta)

    @override
    def draw(self):
        sprite = self._resource_provider.fire[int(self.time * 10) % len(self._resource_provider.fire)]
        self._camera.draw_texture(self.position, Point(1, 1), sprite, repeat=self.size)
        return super().draw()

    @override
    def on_trigger(self, trigger: Actor):
        if isinstance(trigger, Player):
            trigger.take_damage()


ActorRegistry.register_actor(Fire)
