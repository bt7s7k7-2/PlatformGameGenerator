from dataclasses import dataclass, field
from typing import override

from ...game_core.Camera import CameraClient
from ...game_core.ResourceClient import ResourceClient
from ...level_editor.ActorRegistry import ActorRegistry
from ...support.Point import Point
from ...world.Actor import Actor
from ...world.CollisionFlags import CollisionFlags
from ...world.SpriteLayer import SpriteLayer
from ..Player import Player


@dataclass
class Climbable(CameraClient, ResourceClient):
    collision_flags: CollisionFlags = field(default=CollisionFlags.TRIGGER)
    layer: SpriteLayer = field(default=SpriteLayer.BACKGROUND)
    sprite: str = ""
    slide_only: bool = False

    @override
    def draw(self):
        self._camera.draw_texture(self.position, Point.ONE, self._resource_provider.__getattribute__(self.sprite), repeat=self.size)

    def on_trigger(self, trigger: Actor):
        if isinstance(trigger, Player):
            trigger.curr_climbable = self
        return super().on_trigger(trigger)


ActorRegistry.register_actor(Climbable, name_override="Ladder", default_value=Climbable(sprite="ladder_sprite"))
ActorRegistry.register_actor(Climbable, name_override="Pole", default_value=Climbable(sprite="pole_sprite", slide_only=True))
