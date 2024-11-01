from dataclasses import astuple

import pygame

from ..actors.support.GuiElement import GuiElement
from ..game_core.Camera import CameraClient
from ..game_core.InputClient import InputClient
from ..game_core.ResourceClient import ResourceClient
from ..generation.RoomController import RoomController
from ..generation.RoomInfo import NO_KEY
from ..support.constants import HIGHLIGHT_1_COLOR, HIGHLIGHT_2_COLOR, TEXT_BG_COLOR, TEXT_COLOR
from ..support.Direction import Direction
from ..support.Point import Point
from ..world.ServiceActor import ServiceActor


class MapView(CameraClient, InputClient, ResourceClient, GuiElement, ServiceActor):
    room_controller: RoomController | None = None

    def on_added(self):
        self.room_controller = next((x for x in self.world.get_actors() if isinstance(x, RoomController)), None)
        return super().on_added()

    def update(self, delta: float):
        self.show_map = self._input.keys[pygame.K_m]

        if self.room_controller is None or self.universe.map is None:
            return

        for event in self._input.events:
            if event.type == pygame.KEYDOWN and event:
                key = event.key
                direction: Direction | None = None

                if key == pygame.K_j:
                    direction = Direction.LEFT
                elif key == pygame.K_l:
                    direction = Direction.RIGHT
                elif key == pygame.K_i:
                    direction = Direction.UP
                elif key == pygame.K_k:
                    direction = Direction.DOWN

                if direction is not None:
                    self.universe.queue_task(lambda: self.room_controller.switch_rooms(direction))  # type: ignore

    def draw_gui(self):
        if not self.show_map:
            return

        if self.room_controller is None:
            return

        map = self.universe.map
        if map is None:
            return

        start = map.get_start()
        end = Point(0, 0)
        tile_size = 12
        font = self._resource_provider.font

        for room in map.get_rooms():
            point = room.position
            origin = (point - start) * (tile_size * 3)
            surface = self._camera.screen

            if room == self.room_controller.room:
                font.render_to(surface, astuple(origin + Point(tile_size, tile_size)), "X", HIGHLIGHT_1_COLOR, TEXT_BG_COLOR)

            if room.provides_key != NO_KEY:
                font.render_to(surface, astuple(origin), str(room.provides_key), HIGHLIGHT_2_COLOR, TEXT_BG_COLOR)

            font.render_to(surface, astuple(origin + Point(tile_size, 0)), str(room.get_connection(Direction.UP)), TEXT_COLOR, TEXT_BG_COLOR)
            font.render_to(surface, astuple(origin + Point(0, tile_size)), str(room.get_connection(Direction.LEFT)), TEXT_COLOR, TEXT_BG_COLOR)
            font.render_to(surface, astuple(origin + Point(tile_size, tile_size * 2)), str(room.get_connection(Direction.DOWN)), TEXT_COLOR, TEXT_BG_COLOR)
            font.render_to(surface, astuple(origin + Point(tile_size * 2, tile_size)), str(room.get_connection(Direction.RIGHT)), TEXT_COLOR, TEXT_BG_COLOR)

            end = Point.max(origin, end)

        assert self.room_controller.room is not None
        assert self.room_controller.room.prefab is not None
        font.render_to(surface, astuple(Point(0, end.y + tile_size * 3.5)), f"Room: {self.room_controller.room.prefab.name}", TEXT_COLOR, TEXT_BG_COLOR)
