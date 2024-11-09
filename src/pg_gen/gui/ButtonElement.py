from dataclasses import dataclass, field
from typing import Callable, override

from pg_gen.game_core.Camera import Camera

from ..support.Color import Color
from ..support.constants import HIGHLIGHT_1_COLOR, TEXT_COLOR
from .GuiElement import EVENT_CLICK, GuiEvent
from .TextElement import TextElement


@dataclass(kw_only=True)
class ButtonElement(TextElement):
    on_click: Callable[[], None] | None = None
    on_changed: Callable[[bool], None] | None = None
    stateful: bool = False

    bg_opacity: int = field(default=192)

    _checked = False

    @property
    def checked(self):
        return self._checked

    @checked.setter
    def checked(self, value: bool):
        self._checked = value
        self.color = HIGHLIGHT_1_COLOR if self._checked else TEXT_COLOR

    @override
    def render(self, camera: Camera):
        TextElement.render(self, camera)

        camera.draw_placeholder_raw(self.offset, self.computed_size, Color.WHITE.mix(Color.BLACK, 0.5), width=1)

        if self.hovered:
            camera.draw_placeholder_raw(self.offset, self.computed_size, Color.WHITE, opacity=127)

    @override
    def handle_event(self, event: GuiEvent):
        if event.kind == EVENT_CLICK and self.hovered:
            if self.on_click is not None:
                self.on_click()

            if self.stateful:
                self.checked = not self.checked
                if self.on_changed is not None:
                    self.on_changed(self.checked)

            event.handler = self

        super().handle_event(event)
