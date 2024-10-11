from dataclasses import astuple, dataclass
from functools import cached_property
from math import ceil

import pygame
from pygame import Surface

from ..support.Color import Color
from ..support.constants import CAMERA_SCALE
from ..support.Point import Point
from ..world.Actor import Actor
from .Texture import Texture


@dataclass(kw_only=True)
class Camera:
    screen: Surface
    zoom: float = CAMERA_SCALE
    offset: Point = Point.ZERO

    def world_to_screen(self, point: Point):
        return (point - self.offset) * self.zoom

    def screen_to_world(self, point: Point):
        return point * (1 / self.zoom) + self.offset

    def draw_placeholder_raw(self, position: Point, size: Point, color: Color, opacity=255):
        if opacity < 255:
            surface = Surface(astuple(size), flags=pygame.SRCALPHA)
            surface.fill(color.to_pygame_color(opacity))
            self.screen.blit(surface, position.to_pygame_rect(size), Point.ZERO.to_pygame_rect(size))
        else:
            pygame.draw.rect(self.screen, color.to_pygame_color(), position.to_pygame_rect(size))

    def draw_placeholder(self, position: Point, size: Point, color: Color, opacity=255):
        self.draw_placeholder_raw(self.world_to_screen(position), size * self.zoom, color, opacity)

    def draw_texture_raw(self, position: Point, size: Point, texture: Texture, color: Color = Color.WHITE, repeat=Point.ONE, rotate=0.0):
        surface = Surface(astuple(texture.size), flags=pygame.SRCALPHA)

        surface.blit(texture.surface, (0, 0))

        surface = pygame.transform.scale(surface, astuple(size))

        if color != Color.WHITE:
            surface.fill(color.to_pygame_color(), special_flags=pygame.BLEND_RGB_MULT)

        if rotate != 0:
            surface = pygame.transform.rotate(surface, rotate)

        if repeat == Point.ONE:
            self.screen.blit(surface, astuple(position))
            return

        for x in range(ceil(repeat.x)):
            for y in range(ceil(repeat.y)):
                offset = Point(x, y) * size
                fragment_size = Point.min(size, size * repeat - offset)
                self.screen.blit(surface, (position + offset).to_pygame_rect(fragment_size), Point.ZERO.to_pygame_rect(fragment_size))

    def draw_texture(self, position: Point, size: Point, texture: Texture, color: Color = Color.WHITE, repeat=Point.ONE, rotate=0.0):
        self.draw_texture_raw(self.world_to_screen(position), size * self.zoom, texture, color, repeat, rotate)


class CameraClient(Actor):
    @cached_property
    def _camera(self):
        return self.universe.di.inject(Camera)
