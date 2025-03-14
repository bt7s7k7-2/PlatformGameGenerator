from dataclasses import astuple
from typing import override

import pygame

from ..actors.support.GuiRenderer import GuiRenderer
from ..game_core.Camera import CameraClient
from ..game_core.InputClient import InputClient
from ..game_core.ResourceClient import ResourceClient
from ..generation.RoomController import RoomController
from ..generation.RoomInfo import NO_KEY, NO_PICKUP, NOT_CONNECTED, RoomInfo
from ..support.Color import Color
from ..support.constants import HIGHLIGHT_1_COLOR, HIGHLIGHT_2_COLOR, MUTED_COLOR, TEXT_BG_COLOR, TEXT_COLOR
from ..support.Direction import Direction
from ..support.Point import Point
from ..world.ServiceActor import ServiceActor

_LINE_COLOR = Color.CYAN.mix(Color.BLUE, 0.5)


class MapView(CameraClient, InputClient, ResourceClient, GuiRenderer, ServiceActor):
    room_controller: RoomController | None = None
    has_paused = False

    @override
    def on_added(self):
        self.room_controller = next((x for x in self.world.get_actors() if isinstance(x, RoomController)), None)
        if self.has_paused:
            self.world.paused = True
        return super().on_added()

    @override
    def update(self, delta: float):
        self.show_map = self._input.keys[pygame.K_m]
        if not self.show_map:
            if self.has_paused:
                self.world.paused = False
                self.has_paused = False
        else:
            if not self.world.paused and not self.has_paused:
                self.world.paused = True
                self.has_paused = True

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

    @override
    def draw_gui(self):
        if not self.show_map:
            return

        map = self.universe.map
        if map is None:
            return

        start = map.get_start()
        end = Point(0, 0)
        tile_size = 12
        line_size = tile_size * 3 / 2
        font = self._resource_provider.font
        offset = Point(0, 12)

        def get_room_origin(room: RoomInfo):
            point = room.position
            origin = (point - start) * (tile_size * 3) + offset
            return origin

        current_room = self.room_controller.room if self.room_controller else None

        current_room_offset = get_room_origin(current_room) if current_room else Point.ZERO
        offset = Point.min(
            Point(12, 12),
            self._camera.screen_size - (current_room_offset + (Point.ONE * tile_size * 9)),
        )

        surface = self._camera.screen

        for room in map.get_rooms():
            origin = get_room_origin(room)

            self._camera.draw_placeholder_raw(origin - Point.ONE, Point.ONE * (tile_size * 3 + 1), Color.BLACK, opacity=127)
            self._camera.draw_placeholder_raw(origin - Point.ONE, Point.ONE * (tile_size * 3 + 1), Color.WHITE, width=1, opacity=127)

            for direction, line_position, text_position in [
                (Direction.UP, Point(line_size, 0), Point(tile_size, 0)),
                (Direction.LEFT, Point(0, line_size), Point(0, tile_size)),
                (Direction.DOWN, Point(line_size, line_size), Point(tile_size, tile_size * 2)),
                (Direction.RIGHT, Point(line_size, line_size), Point(tile_size * 2, tile_size)),
            ]:
                connection = room.get_connection(direction)
                if connection == NOT_CONNECTED:
                    continue
                size = Point(line_size, 1) if direction.horizontal else Point(1, line_size)
                self._camera.draw_placeholder_raw(origin + line_position, size, _LINE_COLOR)
                if connection > NO_KEY:
                    font.render_to(surface, astuple(origin + text_position), str(connection), TEXT_COLOR, TEXT_BG_COLOR)

            if self.room_controller and room == self.room_controller.room:
                font.render_to(surface, astuple(origin + Point(tile_size, tile_size)), "X", HIGHLIGHT_1_COLOR, TEXT_BG_COLOR)

            font.render_to(surface, astuple(origin + Point(0, tile_size * 2)), str(room.area), MUTED_COLOR, TEXT_BG_COLOR)

            if room.pickup_type != NO_PICKUP:
                font.render_to(surface, astuple(origin), str(room.pickup_type), HIGHLIGHT_2_COLOR, TEXT_BG_COLOR)

            end = Point.max(origin, end)

        if current_room is not None:
            text = ""

            if current_room.prefab is not None:
                text = f"Room: {current_room.prefab.name}; Difficulty: "

            text += str(current_room.difficulty)

            if len(text) > 0:
                font.render_to(surface, astuple(Point(0, 0)), text, TEXT_COLOR, TEXT_BG_COLOR)
