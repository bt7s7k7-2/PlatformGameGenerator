from dataclasses import astuple, dataclass, field

from pygame import Surface

from ..entities.Player import Player
from ..entities.Wall import Wall
from ..game_core.InputState import InputState
from ..game_core.ResourceProvider import ResourceProvider
from ..support.Color import Color
from ..support.constants import JUMP_IMPULSE, ROOM_HEIGHT, ROOM_WIDTH
from ..support.Direction import Direction
from ..support.Point import Point
from ..world.Actor import Actor
from ..world.World import World
from .MapGenerator import NOT_CONNECTED, RoomInfo
from .RoomTrigger import RoomTrigger


@dataclass
class RoomController(Actor):
    room: RoomInfo | None = None

    _input: InputState = field(init=False, repr=False)
    _resource_provider: ResourceProvider | None = field(init=False, repr=False, default=None)

    def __post_init__(self):
        self._input = self.universe.di.inject(InputState)

    def update(self, delta: float):
        if self.room is None:
            return

        if self._input.teleport_up:
            self.switch_rooms(Direction.UP)
        elif self._input.teleport_left:
            self.switch_rooms(Direction.LEFT)
        elif self._input.teleport_right:
            self.switch_rooms(Direction.RIGHT)
        elif self._input.teleport_down:
            self.switch_rooms(Direction.DOWN)

    def switch_rooms(self, direction: Direction):
        assert self.room is not None
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
                self.universe,
                position=Point.ZERO,
                size=Point(ROOM_WIDTH / 2 - entrance_size / 2, 1),
            ),
            Wall(
                self.universe,
                position=Point(ROOM_WIDTH / 2 + entrance_size / 2, 0),
                size=Point(ROOM_WIDTH / 2 - entrance_size / 2, 1),
            ),
            Wall(
                self.universe,
                position=Point(0, 1 + entrance_size),
                size=Point(corridor_length, ROOM_HEIGHT - 1 - entrance_size),
            ),
            Wall(
                self.universe,
                position=Point(ROOM_WIDTH - corridor_length, 1 + entrance_size),
                size=Point(corridor_length, ROOM_HEIGHT - 1 - entrance_size),
            ),
            Wall(
                self.universe,
                position=Point(0, ROOM_HEIGHT - 1),
                size=Point(ROOM_WIDTH / 2 - entrance_size / 2, 1),
            ),
            Wall(
                self.universe,
                position=Point(ROOM_WIDTH / 2 + entrance_size / 2, ROOM_HEIGHT - 1),
                size=Point(ROOM_WIDTH / 2 - entrance_size / 2, 1),
            ),
            Wall(
                self.universe,
                position=Point(corridor_length + gap_size, entrance_size + 1),
                size=Point(ROOM_WIDTH - corridor_length * 2 - gap_size * 2, 1),
            ),
            Wall(
                self.universe,
                position=Point(2, 1 + entrance_size + ROOM_HEIGHT / 3),
                size=Point(corridor_length, 1),
            ),
            Wall(
                self.universe,
                position=Point(ROOM_WIDTH - corridor_length - 2, 1 + entrance_size + ROOM_HEIGHT / 3),
                size=Point(corridor_length, 1),
            ),
        )

        if self.room.get_connection(Direction.LEFT) == NOT_CONNECTED:
            world.add_actor(
                Wall(
                    self.universe,
                    position=Point(0, 1),
                    size=Point(1, entrance_size),
                )
            )
        else:
            world.add_actor(
                RoomTrigger(
                    self.universe,
                    position=Point(-1.5, 1),
                    size=Point(1, entrance_size),
                    room_controller=self,
                    direction=Direction.LEFT,
                )
            )

        if self.room.get_connection(Direction.RIGHT) == NOT_CONNECTED:
            world.add_actor(
                Wall(
                    self.universe,
                    position=Point(ROOM_WIDTH - 1, 1),
                    size=Point(1, entrance_size),
                )
            )
        else:
            world.add_actor(
                RoomTrigger(
                    self.universe,
                    position=Point(ROOM_WIDTH + 0.5, 1),
                    size=Point(1, entrance_size),
                    room_controller=self,
                    direction=Direction.RIGHT,
                )
            )

        if self.room.get_connection(Direction.UP) == NOT_CONNECTED:
            world.add_actor(
                Wall(
                    self.universe,
                    position=Point(ROOM_WIDTH / 2 - entrance_size / 2, 0),
                    size=Point(entrance_size, 1),
                )
            )
        else:
            world.add_actor(
                RoomTrigger(
                    self.universe,
                    position=Point(ROOM_WIDTH / 2 - entrance_size / 2, -1.5),
                    size=Point(entrance_size, 1),
                    room_controller=self,
                    direction=Direction.UP,
                )
            )

        if self.room.get_connection(Direction.DOWN) == NOT_CONNECTED:
            world.add_actor(
                Wall(
                    self.universe,
                    position=Point(ROOM_WIDTH / 2 - entrance_size / 2, ROOM_HEIGHT - 1),
                    size=Point(entrance_size, 1),
                )
            )
        else:
            world.add_actor(
                RoomTrigger(
                    self.universe,
                    position=Point(ROOM_WIDTH / 2 - entrance_size / 2, ROOM_HEIGHT + 0.5),
                    size=Point(entrance_size, 1),
                    room_controller=self,
                    direction=Direction.DOWN,
                )
            )

        player = self.universe.di.try_inject(Player)
        if player is not None:
            world.add_actor(player)

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
        self.universe.world = world

    def draw(self, surface: Surface):
        if not self._input.show_map:
            return

        def draw_overlay():
            self._resource_provider = self._resource_provider or self.universe.di.inject(ResourceProvider)
            map = self.universe.map
            start = map.get_start()
            tile_size = 12
            font = self.universe.di.inject(ResourceProvider).font

            current_room_color = Color.GREEN.to_pygame_color(opacity=127)
            door_color = Color.WHITE.to_pygame_color()
            bgcolor = Color.BLACK.to_pygame_color(opacity=127)

            for room in map.get_rooms():
                point = room.position
                origin = (point - start) * (tile_size * 3)

                if room == self.room:
                    font.render_to(surface, astuple(origin + Point(tile_size, tile_size)), "X", current_room_color, bgcolor)

                font.render_to(surface, astuple(origin + Point(tile_size, 0)), str(room.get_connection(Direction.UP)), door_color, bgcolor)
                font.render_to(surface, astuple(origin + Point(0, tile_size)), str(room.get_connection(Direction.LEFT)), door_color, bgcolor)
                font.render_to(surface, astuple(origin + Point(tile_size, tile_size * 2)), str(room.get_connection(Direction.DOWN)), door_color, bgcolor)
                font.render_to(surface, astuple(origin + Point(tile_size * 2, tile_size)), str(room.get_connection(Direction.RIGHT)), door_color, bgcolor)

        self.universe.queue_task(draw_overlay)
