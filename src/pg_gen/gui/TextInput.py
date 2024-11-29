from dataclasses import astuple, dataclass, field
from itertools import chain
from string import ascii_letters, digits
from typing import Any, Callable, override

import pygame
import pygame.freetype

from pg_gen.game_core.Camera import Camera
from pg_gen.gui.GuiElement import GuiEvent

from ..support.constants import TEXT_BG_COLOR, TEXT_COLOR, TEXT_SELECTION_COLOR
from ..support.Point import Point
from .GuiElement import EVENT_KEY, SelectableElement

_word_characters = set(chain(ascii_letters, digits, ["_"]))


@dataclass(kw_only=True)
class TextInput(SelectableElement):
    cursor_pos = 0
    selection_start = 0
    selection_length = 0
    on_changed: Callable[[str], None] | None = None
    font: pygame.freetype.Font
    placeholder: str | None = None
    color: Any = TEXT_COLOR

    _value: list[str] = field(default_factory=lambda: [])
    _changed: bool = False

    @property
    def value(self):
        return "".join(self._value)

    @value.setter
    def value(self, value: str):
        self._value.clear()
        self._value.extend(value)
        self.cursor_pos = len(value)
        self.selection_start = 0
        self.selection_length = 0

    def move_by_word(self, offset: int, update_selection: bool):
        target_is_word = False
        is_first_iteration = True

        while True:
            read_position = self.cursor_pos - 1 if offset < 0 else self.cursor_pos
            if read_position < 0 or read_position >= len(self._value):
                return

            read_char = self._value[read_position]
            is_word = read_char in _word_characters
            if is_first_iteration:
                is_first_iteration = False
                target_is_word = is_word

            if is_word != target_is_word:
                return

            self.move_cursor(offset, update_selection)

    def is_point_in_selection(self, point: int):
        return self.selection_length > 0 and self.selection_start <= point and point < self.selection_start + self.selection_length

    def move_cursor(self, offset: int, update_selection: bool):
        self.cursor_pos += offset

        if self.cursor_pos < 0:
            self.cursor_pos = 0
            return
        elif self.cursor_pos > len(self._value):
            self.cursor_pos = len(self._value)
            return

        if not update_selection:
            self.selection_length = 0
            return

        if self.selection_length == 0:
            self.selection_start = self.cursor_pos - offset

        expand = not self.is_point_in_selection(self.cursor_pos)

        if expand:
            if offset < 0:
                self.selection_start -= 1

            self.selection_length += 1
        else:
            if offset > 0:
                self.selection_start += 1

            self.selection_length -= 1

    def draw_cursor(self, surface: pygame.Surface, position: Point):
        if not self.selected:
            return

        surface.fill(TEXT_COLOR, position.to_pygame_rect(Point(1, 12)))

    def draw(self, font: pygame.freetype.Font, surface: pygame.Surface, position: Point, start=0):
        target_is_selected = self.is_point_in_selection(start)

        bgcolor = TEXT_SELECTION_COLOR if target_is_selected else TEXT_BG_COLOR
        color = self.color

        if start == 0 and self.cursor_pos == 0:
            self.draw_cursor(surface, position)

        end = -1
        next = -1

        if start >= len(self._value):
            return

        for i in range(start, len(self._value)):
            end = i
            next = i
            is_selected = self.is_point_in_selection(i)
            if is_selected != target_is_selected:
                next = end
                end = i - 1
                break
            if i == self.cursor_pos - 1:
                next = end + 1
                break

        text = "".join(self._value[start : end + 1])
        width = font.get_rect(text).width
        font.render_to(surface, astuple(position), text, color, bgcolor)
        end_position = position + Point.RIGHT * width

        if end == self.cursor_pos - 1:
            self.draw_cursor(surface, end_position)

        if end < len(self._value) - 1:
            self.draw(font, surface, end_position, next)

    def delete(self, offset: int):
        if self.selection_length > 0:
            del self._value[self.selection_start : self.selection_start + self.selection_length]
            self.cursor_pos = self.selection_start
            self.selection_length = 0
            return

        if offset < 0:
            del self._value[self.cursor_pos - 1 : self.cursor_pos]
            self.move_cursor(-1, update_selection=False)
        else:
            del self._value[self.cursor_pos : self.cursor_pos + 1]

        self._changed = True

    def write(self, char: str):
        if len(char) > 1:
            for c in char:
                self.write(c)
            return

        if self.selection_length > 0:
            self.delete(0)

        self._value.insert(self.cursor_pos, char)
        self.cursor_pos += 1
        self._changed = True

    @override
    def update_size(self):
        self.computed_size = Point(10, self.font.size)  # type: ignore
        super().update_size()

    @override
    def handle_event(self, event: GuiEvent):
        if event.kind == EVENT_KEY and self.selected:
            key = event.value.key

            assert event.input is not None
            key_state = event.input.keys
            is_ctrl = key_state[pygame.K_LCTRL]
            is_shift = key_state[pygame.K_LSHIFT]

            if key == pygame.K_LEFT:
                if is_ctrl:
                    self.move_by_word(-1, update_selection=is_shift)
                self.move_cursor(-1, update_selection=is_shift)
            elif key == pygame.K_RIGHT:
                if is_ctrl:
                    self.move_by_word(1, update_selection=is_shift)
                self.move_cursor(1, update_selection=is_shift)
            elif key == pygame.K_a and is_ctrl:
                self.selection_start = 0
                self.selection_length = len(self._value)
            elif key == pygame.K_BACKSPACE:
                if is_ctrl:
                    self.move_by_word(-1, update_selection=True)
                self.delete(-1)
            elif key == pygame.K_DELETE:
                if is_ctrl:
                    self.move_by_word(1, update_selection=True)
                self.delete(1)
            elif key == pygame.K_HOME:
                self.move_cursor(-self.cursor_pos, update_selection=is_shift)
            elif key == pygame.K_END:
                self.move_cursor(len(self._value) - self.cursor_pos, update_selection=is_shift)
            elif key == pygame.K_ESCAPE:
                self.selection_length = 0
            elif key == pygame.K_v and is_ctrl:
                if not pygame.scrap.get_init():
                    pygame.scrap.init()
                for type in pygame.scrap.get_types():
                    if type.startswith("text/plain"):
                        value = pygame.scrap.get(type).decode("utf-8")  # type: ignore
                        self.write(value)
                        break
            elif not is_ctrl:
                char = event.value.unicode
                if len(char) == 1 and char != "\r":
                    self.write(char)

        if self._changed:
            self._changed = False
            self._handle_changed()
        return super().handle_event(event)

    def _handle_changed(self):
        if self.on_changed is not None:
            self.on_changed(self.value)

    @override
    def render(self, camera: Camera):
        super().render(camera)
        if self.placeholder is not None and len(self._value) == 0:
            self.font.render_to(camera.screen, astuple(self.offset), self.placeholder, (127, 127, 127), TEXT_BG_COLOR)
        self.draw(self.font, camera.screen, self.offset)
