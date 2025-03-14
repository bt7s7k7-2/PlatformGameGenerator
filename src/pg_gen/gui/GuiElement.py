from dataclasses import dataclass, field
from typing import Any, override

import pygame

from ..game_core.Camera import Camera
from ..game_core.InputState import InputState
from ..support.Color import Color
from ..support.Point import Axis, Point
from ..support.resolve_intersection import is_intersection

EVENT_LEAVE = 1
EVENT_MOVE = 2
EVENT_CLICK = 3
EVENT_KEY = 4
EVENT_DESELECT = 6


@dataclass
class GuiEvent:
    kind: int
    value: Any = None
    position: Point = Point.ZERO
    handler: "GuiElement | None" = None
    input: InputState | None = None
    pass


@dataclass(kw_only=True, eq=False)
class GuiElement:
    computed_size: Point = Point.ZERO
    size_override: Point = Point.NAN
    offset: Point = Point.ZERO
    translation: Point = Point.ZERO
    bg_color: Color = Color.BLACK
    bg_opacity: int = 0
    hovered = False

    def update_size(self):
        self.computed_size = self.computed_size.merge(self.size_override)

    def layout(self):
        pass

    def handle_event(self, event: GuiEvent):
        if event.kind == EVENT_LEAVE:
            self.hovered = False

        if event.kind == EVENT_MOVE:
            self.hovered = True

    def render(self, camera: Camera):
        if self.bg_opacity > 0:
            camera.draw_placeholder_raw(self.offset, self.computed_size, self.bg_color, self.bg_opacity)

    def update_and_render(self, camera: Camera, input: InputState):
        for event in input.events:
            if event.type == pygame.KEYDOWN:
                self.handle_event(GuiEvent(EVENT_KEY, value=event, input=input))
            elif event.type == pygame.MOUSEMOTION:
                self.handle_event(GuiEvent(EVENT_LEAVE))
                self.handle_event(GuiEvent(EVENT_MOVE, position=Point(*event.pos)))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_event(GuiEvent(EVENT_DESELECT))
                self.handle_event(GuiEvent(EVENT_CLICK, value=event, position=Point(*event.pos)))

        self.update_size()
        self.layout()
        self.render(camera)


@dataclass
class SelectableElement(GuiElement):
    selected: bool = False
    always_selected: bool = False

    @override
    def handle_event(self, event: GuiEvent):
        if event.kind == EVENT_CLICK and self.hovered:
            self.selected = True
            event.handler = self

        if event.kind == EVENT_DESELECT:
            if not self.always_selected:
                self.selected = False

        return super().handle_event(event)


INDEX_NONE = -1


@dataclass
class GuiContainer(GuiElement):
    axis: Axis
    children: list[GuiElement] = field(default_factory=lambda: [])

    @override
    def update_size(self):
        self.computed_size = Point.ZERO

        main_axis = self.axis
        cross_axis = self.axis.cross

        for child in self.children:
            child.update_size()
            extend = child.computed_size[main_axis]
            min = child.computed_size[cross_axis]

            self.computed_size = Point.max(self.computed_size + extend, min)

        super().update_size()

    @override
    def layout(self):
        offset = self.offset
        for child in self.children:
            child.offset = offset
            child.layout()
            offset += child.computed_size[self.axis]

        super().layout()

    @override
    def render(self, camera: Camera):
        super().render(camera)
        for child in self.children:
            child.render(camera)

    @override
    def handle_event(self, event: GuiEvent):
        if event.kind == EVENT_MOVE:
            index = next((child for child in self.children if is_intersection(child.offset, child.computed_size, event.position, Point.ZERO)), None)
            if index is not None:
                index.handle_event(event)
            return

        for child in self.children:
            child.handle_event(event)

        return super().handle_event(event)
