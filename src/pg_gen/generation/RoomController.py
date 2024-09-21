from dataclasses import astuple, dataclass, field

from pygame import Surface

from ..game_core.InputState import InputState
from ..game_core.ResourceProvider import ResourceProvider
from ..support.Color import Color
from ..support.Direction import Direction
from ..support.Point import Point
from ..world.Actor import Actor
from ..world.World import World
from .MapGenerator import RoomInfo


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

        teleport = Point.ZERO

        if self._input.teleport_up:
            teleport += Point.UP
        if self._input.teleport_left:
            teleport += Point.LEFT
        if self._input.teleport_right:
            teleport += Point.RIGHT
        if self._input.teleport_down:
            teleport += Point.DOWN

        if teleport == Point.ZERO:
            return

        self.switch_rooms(teleport)

    def switch_rooms(self, offset: Point):
        assert self.room is not None
        next_position = self.room.position + offset
        if not self.universe.map.has_room(next_position):
            print(f"Tried to teleport to invalid room {next_position}")
            return

        next_room = self.universe.map.get_room(next_position)
        self.universe.queue_task(lambda: RoomController(self.universe, room=next_room).initialize_room())

    def initialize_room(self):
        assert self.room is not None
        world = World(self.universe)

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
            door_color = Color.WHITE.to_pygame_color(opacity=127)
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
