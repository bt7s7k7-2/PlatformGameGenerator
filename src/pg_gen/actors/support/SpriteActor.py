from dataclasses import dataclass

from ...game_core.Camera import CameraClient
from ...game_core.ResourceClient import ResourceClient
from ...support.Color import Color


@dataclass
class SpriteActor(ResourceClient, CameraClient):
    rotation = 0
    flip = False
    sprite: str | None = None
    debug_draw_colliders: bool = False

    def draw(self):
        if self.sprite is None:
            return

        sprite = self._resource_provider.__getattribute__(self.sprite)
        self._camera.draw_texture(self.position, self.size, sprite, rotate=self.rotation, flip_x=self.flip)

        if self.debug_draw_colliders:
            for position, size in self.get_colliders():
                self._camera.draw_placeholder(position, size, Color.GREEN)
