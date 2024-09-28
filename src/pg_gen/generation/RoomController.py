from dataclasses import astuple, dataclass

import pygame
from pygame import Surface

from ..entities.Door import Door
from ..entities.GuiElement import GuiElement
from ..entities.Key import Key
from ..entities.Player import Player
from ..entities.Wall import Wall
from ..game_core.InputClient import InputClient
from ..game_core.ResourceClient import ResourceClient
from ..support.constants import HIGHLIGHT_1_COLOR, HIGHLIGHT_2_COLOR, JUMP_IMPULSE, ROOM_HEIGHT, ROOM_WIDTH, TEXT_BG_COLOR, TEXT_COLOR
from ..support.Direction import Direction
from ..support.Point import Point
from ..world.World import World
from .RoomInfo import NO_KEY, NOT_CONNECTED, RoomInfo
from .RoomTrigger import RoomTrigger


@dataclass
class RoomController(GuiElement, ResourceClient, InputClient):
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

        entrance_size = 3
        gap_size = 4
        corridor_length = 2
        world.add_actors(
            Wall(
                position=Point.ZERO,
                size=Point(ROOM_WIDTH / 2 - entrance_size / 2, 1),
            ),
            Wall(
                position=Point(ROOM_WIDTH / 2 + entrance_size / 2, 0),
                size=Point(ROOM_WIDTH / 2 - entrance_size / 2, 1),
            ),
            Wall(
                position=Point(0, 1 + entrance_size),
                size=Point(corridor_length, ROOM_HEIGHT - 1 - entrance_size),
            ),
            Wall(
                position=Point(ROOM_WIDTH - corridor_length, 1 + entrance_size),
                size=Point(corridor_length, ROOM_HEIGHT - 1 - entrance_size),
            ),
            Wall(
                position=Point(0, ROOM_HEIGHT - 1),
                size=Point(ROOM_WIDTH / 2 - entrance_size / 2, 1),
            ),
            Wall(
                position=Point(ROOM_WIDTH / 2 + entrance_size / 2, ROOM_HEIGHT - 1),
                size=Point(ROOM_WIDTH / 2 - entrance_size / 2, 1),
            ),
            Wall(
                position=Point(corridor_length + gap_size, entrance_size + 1),
                size=Point(ROOM_WIDTH - corridor_length * 2 - gap_size * 2, 1),
            ),
            Wall(
                position=Point(2, 1 + entrance_size + ROOM_HEIGHT / 3),
                size=Point(corridor_length, 1),
            ),
            Wall(
                position=Point(ROOM_WIDTH - corridor_length - 2, 1 + entrance_size + ROOM_HEIGHT / 3),
                size=Point(corridor_length, 1),
            ),
        )

        if self.room.get_connection(Direction.LEFT) == NOT_CONNECTED:
            world.add_actor(
                Wall(
                    position=Point(0, 1),
                    size=Point(1, entrance_size),
                )
            )
        else:
            world.add_actor(
                RoomTrigger(
                    position=Point(-1.5, 1),
                    size=Point(1, entrance_size),
                    room_controller=self,
                    direction=Direction.LEFT,
                )
            )

        if self.room.get_connection(Direction.RIGHT) == NOT_CONNECTED:
            world.add_actor(
                Wall(
                    position=Point(ROOM_WIDTH - 1, 1),
                    size=Point(1, entrance_size),
                )
            )
        else:
            world.add_actor(
                RoomTrigger(
                    position=Point(ROOM_WIDTH + 0.5, 1),
                    size=Point(1, entrance_size),
                    room_controller=self,
                    direction=Direction.RIGHT,
                )
            )

        if self.room.get_connection(Direction.UP) == NOT_CONNECTED:
            world.add_actor(
                Wall(
                    position=Point(ROOM_WIDTH / 2 - entrance_size / 2, 0),
                    size=Point(entrance_size, 1),
                )
            )
        else:
            world.add_actor(
                RoomTrigger(
                    position=Point(ROOM_WIDTH / 2 - entrance_size / 2, -1.5),
                    size=Point(entrance_size, 1),
                    room_controller=self,
                    direction=Direction.UP,
                )
            )

        if self.room.get_connection(Direction.DOWN) == NOT_CONNECTED:
            world.add_actor(
                Wall(
                    position=Point(ROOM_WIDTH / 2 - entrance_size / 2, ROOM_HEIGHT - 1),
                    size=Point(entrance_size, 1),
                )
            )
        else:
            world.add_actor(
                RoomTrigger(
                    position=Point(ROOM_WIDTH / 2 - entrance_size / 2, ROOM_HEIGHT + 0.5),
                    size=Point(entrance_size, 1),
                    room_controller=self,
                    direction=Direction.DOWN,
                )
            )

        if self.room.provides_key != NO_KEY:
            world.add_actor(Key(key_type=self.room.provides_key, position=Point(ROOM_WIDTH / 2 - 0.5, entrance_size - 1), room=self.room))

        next_flag = 0

        def get_next_flag():
            assert self.room is not None
            nonlocal next_flag

            flag = next_flag
            next_flag += 1

            if len(self.room.persistent_flags) <= flag:
                self.room.persistent_flags.append(None)

            return flag

        if self.room.get_connection(Direction.LEFT) > NO_KEY:
            world.add_actor(
                Door(
                    position=Point(1, 1),
                    room=self.room,
                    key_type=self.room.get_connection(Direction.LEFT),
                    flag_index=get_next_flag(),
                )
            )

        if self.room.get_connection(Direction.RIGHT) > NO_KEY:
            world.add_actor(
                Door(
                    position=Point(ROOM_WIDTH - 2, 1),
                    room=self.room,
                    key_type=self.room.get_connection(Direction.RIGHT),
                    flag_index=get_next_flag(),
                )
            )

        player = self.universe.di.try_inject(Player)
        if player is not None:
            player.transfer_world(world)

            if entrance == Direction.LEFT or entrance == Direction.RIGHT:
                player.position = (
                    Point(
                        ROOM_WIDTH / 2 - ((player.position.x + player.size.x / 2) - ROOM_WIDTH / 2) - player.size.x / 2,
                        player.position.y,
                    )
                    - Point.from_direction(entrance) * 0.1
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

    def draw_gui(self, surface: Surface):
        if not self.show_map:
            return

        map = self.universe.map
        if map is None:
            return

        start = map.get_start()
        tile_size = 12
        font = self._resource_provider.font

        for room in map.get_rooms():
            point = room.position
            origin = (point - start) * (tile_size * 3)

            if room == self.room:
                font.render_to(surface, astuple(origin + Point(tile_size, tile_size)), "X", HIGHLIGHT_1_COLOR, TEXT_BG_COLOR)

            if room.provides_key != NO_KEY:
                font.render_to(surface, astuple(origin), str(room.provides_key), HIGHLIGHT_2_COLOR, TEXT_BG_COLOR)

            font.render_to(surface, astuple(origin + Point(tile_size, 0)), str(room.get_connection(Direction.UP)), TEXT_COLOR, TEXT_BG_COLOR)
            font.render_to(surface, astuple(origin + Point(0, tile_size)), str(room.get_connection(Direction.LEFT)), TEXT_COLOR, TEXT_BG_COLOR)
            font.render_to(surface, astuple(origin + Point(tile_size, tile_size * 2)), str(room.get_connection(Direction.DOWN)), TEXT_COLOR, TEXT_BG_COLOR)
            font.render_to(surface, astuple(origin + Point(tile_size * 2, tile_size)), str(room.get_connection(Direction.RIGHT)), TEXT_COLOR, TEXT_BG_COLOR)
