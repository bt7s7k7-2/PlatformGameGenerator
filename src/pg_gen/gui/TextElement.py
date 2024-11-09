from dataclasses import astuple, dataclass
from typing import Any, override

import pygame.freetype

from ..game_core.Camera import Camera
from ..support.constants import TEXT_COLOR
from ..support.Point import Point
from .GuiElement import GuiElement


@dataclass
class TextElement(GuiElement):
    text: str
    font: pygame.freetype.Font
    color: Any = TEXT_COLOR

    @override
    def update_size(self):
        if self.computed_size.y == 0:
            size = self.font.get_rect(self.text)
            self.computed_size = Point(size.width + 4, max(self.font.size, size.height + 4))  # type: ignore
        super().update_size()

    @override
    def render(self, camera: Camera):
        super().render(camera)
        size = self.font.render_to(camera.screen, astuple(self.offset + Point(2, 2)), self.text, self.color)
        self.computed_size = Point(size.width + 4, max(self.font.size, size.height + 4))  # type: ignore
