from dataclasses import dataclass, field
from typing import override

from ...game_core.Camera import CameraClient
from ...game_core.ResourceClient import ResourceClient
from ...support.Color import Color
from ...world.SpriteLayer import SpriteLayer


@dataclass
class SpriteActor(ResourceClient, CameraClient):
    rotation = 0
    flip = False
    sprite: str | None = None
    debug_draw_colliders: bool = False
    layer: SpriteLayer = field(default=SpriteLayer.NORMAL)
    animation_speed: float = 0.0
    animation_timer: float = 0.0
    tint: Color = Color.WHITE

    @override
    def update(self, delta: float):
        if self.animation_speed != 0:
            self.animation_timer += delta * self.animation_speed
        return super().update(delta)

    @override
    def draw(self):
        if self.sprite is None:
            return

        sprite = self._resource_provider.__getattribute__(self.sprite)
        if isinstance(sprite, list):
            if self.animation_timer >= len(sprite):
                self.animation_timer = self.animation_timer % 1
            self._camera.draw_texture(self.position, self.size, sprite[int(self.animation_timer)], rotate=self.rotation, flip_x=self.flip, color=self.tint)
        else:
            self._camera.draw_texture(self.position, self.size, sprite, rotate=self.rotation, flip_x=self.flip, color=self.tint)

        if self.debug_draw_colliders:
            for position, size in self.get_colliders():
                self._camera.draw_placeholder(position, size, Color.GREEN)

        return super().draw()
