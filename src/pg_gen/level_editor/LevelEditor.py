from dataclasses import astuple, dataclass, field
from typing import List

import pygame
from pygame import Surface

from ..entities.GuiElement import GuiElement
from ..game_core.InputClient import InputClient
from ..game_core.ResourceClient import ResourceClient
from ..support.constants import CAMERA_SCALE, HIGHLIGHT_1_COLOR, TEXT_BG_COLOR, TEXT_COLOR
from ..support.Point import Point
from ..support.TextInput import TextInput
from ..world.Actor import Actor
from .ActorRegistry import ActorRegistry, ActorType


@dataclass
class LevelEditor(GuiElement, ResourceClient, InputClient):
    _text_input: TextInput = field(init=False, repr=False, default_factory=lambda: TextInput())
    _search_results: List[ActorType] = field(init=False, repr=False, default_factory=lambda: [])
    _managed_actors: List[Actor] = field(init=False, default_factory=lambda: [])

    _selected_actor_type: ActorType | None = None
    _design_mode: bool = True

    def draw_gui(self, surface: Surface):
        start = Point(10, 10)
        line_offset = Point(0, 12)
        self._text_input.draw(self._resource_provider.font, surface, start)
        start += line_offset

        for type in self._search_results:
            self._resource_provider.font.render_to(
                surface,
                dest=astuple(start),
                text=type.name,
                fgcolor=HIGHLIGHT_1_COLOR if type == self._selected_actor_type else TEXT_COLOR,
                bgcolor=TEXT_BG_COLOR,
            )

            start += line_offset

    def spawn_actor(self, actor_type: ActorType, position: Point):
        actor = actor_type.create_instance()
        position -= actor.size * 0.5
        position = (position * 2).round() * 0.5
        actor.position = position
        self.world.add_actor(actor)
        self._managed_actors.append(actor)

    def update(self, delta: float):
        for event in self._input.events:
            self._text_input.update(event, self._input.keys)

            if self._selected_actor_type is None:
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    index = self._search_results.index(self._selected_actor_type)
                    if index + 1 < len(self._search_results):
                        self._selected_actor_type = self._search_results[index + 1]
                elif event.key == pygame.K_UP:
                    index = self._search_results.index(self._selected_actor_type)
                    if index - 1 >= 0:
                        self._selected_actor_type = self._search_results[index - 1]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if event.button == pygame.BUTTON_RIGHT:
                    self.spawn_actor(self._selected_actor_type, Point(x, y) * (1 / CAMERA_SCALE))
                elif event.button == pygame.BUTTON_LEFT:
                    pass

        count = 0
        self._search_results.clear()

        for name, actor_type in ActorRegistry.get_actor_types():
            if count > 5:
                break

            if self._text_input.value.lower() not in name.lower():
                continue

            count += 1
            self._search_results.append(actor_type)

        if self._selected_actor_type not in self._search_results:
            self._selected_actor_type = self._search_results[0] if len(self._search_results) > 0 else None
