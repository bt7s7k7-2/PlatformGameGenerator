from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property, partial
from math import nan
from typing import Any, Callable, override

import pygame
import pygame.freetype

from ..support.constants import HIGHLIGHT_2_COLOR
from ..support.ObjectManifest import AttributeHandle, ObjectManifest, ObjectManifestParser
from ..support.Point import Axis, Point
from .ButtonElement import ButtonElement
from .CheckboxElement import CheckboxElement
from .GuiElement import GuiContainer
from .ListInput import ListInput
from .TextElement import TextElement
from .TextInput import TextInput


@dataclass(kw_only=True)
class ObjectInput[T](ObjectManifestParser, GuiContainer):
    value: T
    manifest: ObjectManifest
    font: pygame.freetype.Font
    axis: Axis = field(default=Axis.COLUMN)
    on_changed: Callable[[], None] | None = None

    @cached_property
    def attributes(self):
        return AttributeHandle.from_manifest(self.value, self.manifest)

    def handle_changed(self, attribute: AttributeHandle, value: Any):
        if value is not None:
            attribute.setter(value)

        if self.on_changed is not None:
            self.on_changed()

    @override
    def handle_string(self, attribute: AttributeHandle):
        text_input = TextInput(font=self.font, on_changed=partial(self.handle_changed, attribute))
        text_input.value = attribute.getter()
        self._build_host(attribute).children.append(text_input)

    @override
    def handle_bool(self, attribute: AttributeHandle):
        self._build_host(attribute).children.append(CheckboxElement(checked=attribute.getter(), on_changed=partial(self.handle_changed, attribute)))

    @override
    def handle_list(self, attribute: AttributeHandle):
        self._build_host(attribute).children.append(ListInput(font=self.font, value=attribute.getter(), on_changed=partial(self.handle_changed, attribute, None)))

    @override
    def handle_enum(self, elements: dict[str, Enum], attribute: AttributeHandle):
        buttons: list[ButtonElement] = []
        host = self._build_host(attribute)

        def on_click(button: ButtonElement, value: Enum):
            self.handle_changed(attribute, value)
            button.checked = True
            for other_button in buttons:
                if other_button is button:
                    continue
                other_button.checked = False

        for name, value in elements.items():
            button = ButtonElement(font=self.font, text=name)
            button.on_click = partial(on_click, button, value)
            button.checked = attribute.getter() == value
            buttons.append(button)
            host.children.append(button)

    @override
    def handle_unknown(self, attribute: AttributeHandle):
        self._build_host(attribute).children.append(TextElement(font=self.font, color=HIGHLIGHT_2_COLOR, text="?" + type.__name__))

    def _build_host(self, attribute: AttributeHandle):
        host = GuiContainer(
            axis=Axis.ROW,
            children=[
                TextElement(text=attribute.name, font=self.font, size_override=Point(100, nan)),
            ],
        )

        self.children.append(host)
        return host

    def __post_init__(self):
        self.parse(self.attributes)
