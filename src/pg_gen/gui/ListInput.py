from dataclasses import dataclass, field
from functools import partial
from typing import Callable

import pygame
import pygame.freetype

from ..support.Point import Axis
from .ButtonElement import ButtonElement
from .GuiElement import GuiContainer
from .TextInput import TextInput


@dataclass(kw_only=True)
class ListInput(GuiContainer):
    value: list[str]
    font: pygame.freetype.Font
    on_changed: Callable[[], None] | None = None

    axis: Axis = field(default=Axis.COLUMN)

    _inputs: list[TextInput] = field(default_factory=lambda: [])

    def handle_change(self, index: int, value: str):
        self.value[index] = value
        if self.on_changed is not None:
            self.on_changed()

    def handle_delete(self, index: int):
        self.value.pop(index)
        self.update_inputs()
        if self.on_changed is not None:
            self.on_changed()

    def handle_add(self):
        self.value.append("")
        self.update_inputs()
        if self.on_changed is not None:
            self.on_changed()

    def update_inputs(self):
        while len(self._inputs) > len(self.value):
            self.children.pop()
            self._inputs.pop()

        while len(self._inputs) < len(self.value):
            index = len(self._inputs)
            input = TextInput(font=self.font, placeholder=f"[{index}]", on_changed=partial(self.handle_change, index))
            button = ButtonElement(text="-", font=self.font, on_click=partial(self.handle_delete, index))

            self._inputs.append(input)
            self.children.append(GuiContainer(axis=Axis.ROW, children=[button, input]))

        for index, child in enumerate(self._inputs):
            child.value = self.value[index]

    def __post_init__(self):
        self.children.append(ButtonElement(text="+", font=self.font, on_click=self.handle_add))
        self.update_inputs()
