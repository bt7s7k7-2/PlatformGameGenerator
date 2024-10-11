from dataclasses import dataclass

from ...game_core.Camera import CameraClient
from ...game_core.ResourceClient import ResourceClient


@dataclass
class SpriteActor(ResourceClient, CameraClient):
    rotation = 0
    sprite: str | None = None

    def draw(self):
        if self.sprite is None:
            return

        sprite = self._resource_provider.__getattribute__(self.sprite)
        self._camera.draw_texture(self.position, self.size, sprite, rotate=self.rotation)
