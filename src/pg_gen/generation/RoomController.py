from dataclasses import astuple, dataclass

import pygame

from ..actors.Player import Player
from ..actors.support.GuiElement import GuiElement
from ..game_core.Camera import CameraClient
from ..game_core.InputClient import InputClient
from ..game_core.ResourceClient import ResourceClient
from ..support.constants import HIGHLIGHT_1_COLOR, HIGHLIGHT_2_COLOR, JUMP_IMPULSE, ROOM_HEIGHT, ROOM_WIDTH, TEXT_BG_COLOR, TEXT_COLOR
from ..support.Direction import Direction
from ..support.Point import Point
from ..world.World import World
from .RoomInfo import NO_KEY, RoomInfo


@dataclass
class RoomController(GuiElement, ResourceClient, InputClient, CameraClient):
    room: RoomInfo | None = None
    show_map = False

    def update(self, delta: float):
        self.show_map = self._input.keys[pygame.K_m]

        if self.room is None or self.universe.map is None:
            return

        for event in self._input.events:
            if event.type == pygame.KEYDOWN and event:
                key = event.key

                if key == pygame.K_j:
                    self.switch_rooms(Direction.LEFT)
                elif key == pygame.K_l:
                    self.switch_rooms(Direction.RIGHT)
                elif key == pygame.K_i:
                    self.switch_rooms(Direction.UP)
                elif key == pygame.K_k:
                    self.switch_rooms(Direction.DOWN)

    def switch_rooms(self, direction: Direction):
        assert self.room is not None
        assert self.universe.map is not None

        offset = Point.from_direction(direction)
        next_position = self.room.position + offset
        if not self.universe.map.has_room(next_position):
            print(f"Tried to teleport to invalid room {next_position}")
            return

        next_room = self.universe.map.get_room(next_position)
        self.universe.queue_task(lambda: RoomController(self.universe, room=next_room).initialize_room(direction.invert()))

    def initialize_room(self, entrance: Direction | None = None):
        assert self.room is not None
        world = World(self.universe)

        assert self.room.prefab is not None
        self.room.prefab.instantiate(self.room, self, world)

        player = self.universe.di.try_inject(Player)
        if player is not None:
            player.transfer_world(world)

            if entrance == Direction.LEFT or entrance == Direction.RIGHT:
                player.position = (
                    Point(
                        ROOM_WIDTH / 2 - ((player.position.x + player.size.x / 2) - ROOM_WIDTH / 2) - player.size.x / 2,
                        player.position.y,
                    )
                    - Point.from_direction(entrance) * 0.5
                )
            elif entrance == Direction.UP or entrance == Direction.DOWN:
                player.position = (
                    Point(
                        player.position.x,
                        ROOM_HEIGHT / 2 - ((player.position.y + player.size.y / 2) - ROOM_HEIGHT / 2) - player.size.y / 2,
                    )
                    - Point.from_direction(entrance) * 1
                )

            if entrance == Direction.DOWN:
                player.velocity = Point(player.velocity.x, -JUMP_IMPULSE)

        world.add_actor(self)
        self.universe.set_world(world)

    def draw_gui(self):
        if not self.show_map:
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

            if room == self.room:
                font.render_to(surface, astuple(origin + Point(tile_size, tile_size)), "X", HIGHLIGHT_1_COLOR, TEXT_BG_COLOR)

            if room.provides_key != NO_KEY:
                font.render_to(surface, astuple(origin), str(room.provides_key), HIGHLIGHT_2_COLOR, TEXT_BG_COLOR)

            font.render_to(surface, astuple(origin + Point(tile_size, 0)), str(room.get_connection(Direction.UP)), TEXT_COLOR, TEXT_BG_COLOR)
            font.render_to(surface, astuple(origin + Point(0, tile_size)), str(room.get_connection(Direction.LEFT)), TEXT_COLOR, TEXT_BG_COLOR)
            font.render_to(surface, astuple(origin + Point(tile_size, tile_size * 2)), str(room.get_connection(Direction.DOWN)), TEXT_COLOR, TEXT_BG_COLOR)
            font.render_to(surface, astuple(origin + Point(tile_size * 2, tile_size)), str(room.get_connection(Direction.RIGHT)), TEXT_COLOR, TEXT_BG_COLOR)

            end = Point.max(origin, end)

        assert self.room is not None
        assert self.room.prefab is not None
        font.render_to(surface, astuple(Point(0, end.y + tile_size * 3.5)), f"Room: {self.room.prefab.name}", TEXT_COLOR, TEXT_BG_COLOR)
