from dataclasses import astuple, dataclass, field

from pygame import Surface

from ..game_core.InputState import InputState
from ..game_core.ResourceProvider import ResourceProvider
from ..support.Color import Color
from ..support.Direction import Direction
from ..support.Point import Point
from ..world.Actor import Actor
from .MapGenerator import RoomInfo


@dataclass
class RoomController(Actor):
    room: RoomInfo | None = None

    _input: InputState = field(init=False, repr=False)
    _resource_provider: ResourceProvider | None = field(init=False, repr=False, default=None)

    def __post_init__(self):
        self._input = self.universe.di.inject(InputState)

    def draw(self, surface: Surface):
        if not self._input.show_map:
            return

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
