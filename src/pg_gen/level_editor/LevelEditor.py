from dataclasses import astuple, dataclass, field
from typing import List, Type

import pygame
from pygame import Surface

from ..entities.GuiElement import GuiElement
from ..game_core.InputClient import InputClient
from ..game_core.ResourceClient import ResourceClient
from ..support.constants import HIGHLIGHT_1_COLOR, TEXT_BG_COLOR, TEXT_COLOR
from ..support.Point import Point
from ..support.TextInput import TextInput
from ..world.Actor import Actor
from .ActorRegistry import ActorRegistry


@dataclass
class LevelEditor(GuiElement, ResourceClient, InputClient):
    _text_input: TextInput = field(init=False, repr=False, default_factory=lambda: TextInput())
    _actor_list: List[Type[Actor]] = field(init=False, repr=False, default_factory=lambda: [])

    _selected_actor_type: Type[Actor] | None = None
    _design_mode: bool = True

    def draw_gui(self, surface: Surface):
        start = Point(10, 10)
        line_offset = Point(0, 12)
        self._text_input.draw(self._resource_provider.font, surface, start)
        start += line_offset

        for type in self._actor_list:
            self._resource_provider.font.render_to(
                surface,
                dest=astuple(start),
                text=type.__name__,
                fgcolor=HIGHLIGHT_1_COLOR if type == self._selected_actor_type else TEXT_COLOR,
                bgcolor=TEXT_BG_COLOR,
            )

            start += line_offset

    def update(self, delta: float):
        for event in self._input.events:
            self._text_input.update(event, self._input.keys)

            if self._selected_actor_type is None:
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    index = self._actor_list.index(self._selected_actor_type)
                    if index + 1 < len(self._actor_list):
                        self._selected_actor_type = self._actor_list[index + 1]
                elif event.key == pygame.K_UP:
                    index = self._actor_list.index(self._selected_actor_type)
                    if index - 1 >= 0:
                        self._selected_actor_type = self._actor_list[index - 1]

        count = 0
        self._actor_list.clear()

        for name, actor_type in ActorRegistry.get_actor_types():
            if count > 5:
                break

            if self._text_input.value.lower() not in name.lower():
                continue

            count += 1
            self._actor_list.append(actor_type)

        if self._selected_actor_type not in self._actor_list:
            self._selected_actor_type = self._actor_list[0] if len(self._actor_list) > 0 else None
