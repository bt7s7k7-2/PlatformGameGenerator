from dataclasses import astuple
from itertools import chain
from string import ascii_letters, digits
from typing import List

import pygame
import pygame.freetype

from .constants import TEXT_BG_COLOR, TEXT_COLOR, TEXT_SELECTION_COLOR
from .Point import Point

_word_characters = set(chain(ascii_letters, digits, ["_"]))


class TextInput:
    cursor_pos = 0
    selection_start = 0
    selection_length = 0

    @property
    def value(self):
        return "".join(self._value)

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
        surface.fill(TEXT_COLOR, position.to_pygame_rect(Point(1, 12)))

    def draw(self, font: pygame.freetype.Font, surface: pygame.Surface, position: Point, start=0):
        target_is_selected = self.is_point_in_selection(start)

        bgcolor = TEXT_SELECTION_COLOR if target_is_selected else TEXT_BG_COLOR
        color = TEXT_COLOR

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

    def write(self, char: str):
        if self.selection_length > 0:
            self.delete(0)

        self._value.insert(self.cursor_pos, char)
        self.cursor_pos += 1

    def update(self, event: pygame.event.Event, key_state: pygame.key.ScancodeWrapper):
        if event.type == pygame.KEYDOWN:
            key = event.key

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
            elif not is_ctrl:
                char = event.unicode
                if len(char) == 1:
                    self.write(char)

    def __init__(self) -> None:
        self._value: List[str] = []
        pass
