from typing import override

from ..game_core.Camera import CameraClient
from ..level_editor.ActorRegistry import ActorRegistry
from ..support.Color import Color
from .support.ConfigurableObject import ConfigurableObject


class Socket(CameraClient, ConfigurableObject):
    @override
    def draw(self):
        self._camera.draw_placeholder(self.position, self.size, Color.YELLOW, width=1)


ActorRegistry.register_actor(Socket)
