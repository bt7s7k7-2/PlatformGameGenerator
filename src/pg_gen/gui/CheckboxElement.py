from dataclasses import dataclass
from typing import Callable, override

from pg_gen.game_core.Camera import Camera
from pg_gen.gui.GuiElement import GuiEvent

from ..support.Color import Color
from ..support.Point import Point
from .GuiElement import EVENT_CLICK, GuiElement


@dataclass(kw_only=True)
class CheckboxElement(GuiElement):
    checked: bool = False
    on_changed: Callable[[bool], None] | None = None

    @override
    def update_size(self):
        self.computed_size = Point(10, 10)
        return super().update_size()

    @override
    def handle_event(self, event: GuiEvent):
        if event.kind == EVENT_CLICK and self.hovered:
            self.checked = not self.checked
            event.handler = self
            if self.on_changed is not None:
                self.on_changed(self.checked)

        super().handle_event(event)

    @override
    def render(self, camera: Camera):
        camera.draw_placeholder_raw(self.offset, self.computed_size, Color.WHITE, width=1)

        if self.checked:
            camera.draw_placeholder_raw(self.offset + Point(3, 3), self.computed_size - Point(6, 6), Color.GREEN)

        if self.hovered:
            camera.draw_placeholder_raw(self.offset, self.computed_size, Color.WHITE, opacity=127)

        super().render(camera)
