from dataclasses import dataclass, field
from typing import Callable, override

import pygame
import pygame.freetype

from pg_gen.gui.GuiElement import GuiEvent

from ..support.constants import HIGHLIGHT_1_COLOR
from ..support.Point import Axis
from .GuiElement import EVENT_KEY, GuiContainer
from .TextElement import TextElement
from .TextInput import TextInput


@dataclass(kw_only=True)
class SearchInput[T](GuiContainer):
    search_function: Callable[[], list[T]]
    get_label: Callable[[T], str]
    on_changed: Callable[[T | None], None]
    max_results: int = 0
    search: TextInput
    selected: T | None = None
    axis: Axis = field(default=Axis.COLUMN)

    @override
    def update_size(self):
        if len(self.children) == 0:
            self.children.append(self.search)
            self.update_search(None)

        super().update_size()

    def update_search(self, event: GuiEvent | None):
        while len(self.children) > 1:
            self.children.pop()

        count = 0
        query = self.search.value.lower()
        results: list[T] = []

        for result in self.search_function():
            if self.max_results != 0 and count > self.max_results:
                break

            name = self.get_label(result)
            if query not in name.lower():
                continue

            count += 1
            results.append(result)

        if self.selected not in results:
            self.selected = results[0] if len(results) > 0 else None

        if event is not None:
            if event.value.key == pygame.K_DOWN:
                if self.selected is not None:
                    index = results.index(self.selected)
                    if index + 1 < len(results):
                        self.selected = results[index + 1]
            elif event.value.key == pygame.K_UP:
                if self.selected is not None:
                    index = results.index(self.selected)
                    if index - 1 >= 0:
                        self.selected = results[index - 1]

        for result in results:
            text = TextElement(font=self.search.font, text=self.get_label(result))
            if result == self.selected:
                text.color = HIGHLIGHT_1_COLOR
            self.children.append(text)

        self.on_changed(self.selected)

    @override
    def handle_event(self, event: GuiEvent):
        super().handle_event(event)

        if event.kind == EVENT_KEY and self.search.selected:
            self.update_search(event)
