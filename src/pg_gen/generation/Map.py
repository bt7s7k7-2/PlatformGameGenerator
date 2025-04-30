from copy import copy
from dataclasses import dataclass, field

from pg_gen.generation.AreaInfo import AreaInfo

from ..support.Point import Point
from .RoomInfo import RoomInfo


@dataclass
class Map:
    min_x = 0
    min_y = 0
    max_x = 0
    max_y = 0

    room_list: list[RoomInfo] = field(default_factory=lambda: [])
    rooms: dict[Point, RoomInfo] = field(default_factory=lambda: {})
    areas: dict[int, AreaInfo] = field(default_factory=lambda: {})

    altars: list[Point] = field(default_factory=lambda: [])
    portal: Point | None = None

    required_keys: list[tuple[int, int]] = field(default_factory=lambda: [])

    def add_key_requirement(self, max_depth: int, key: int):
        self.required_keys.append((max_depth, key))

    def get_start(self):
        return Point(self.min_x, self.min_y)

    def get_size(self):
        return Point(self.max_x - self.min_x, self.max_y - self.min_y)

    def has_room(self, position: Point):
        return position in self.rooms

    def get_room(self, position: Point):
        return self.rooms[position]

    def get_rooms(self):
        return iter(self.rooms.values())

    def add_room(self, room: RoomInfo):
        position = room.position

        if position.x < self.min_x:
            self.min_x = position.x

        if position.y < self.min_y:
            self.min_y = position.y

        if position.x > self.max_x:
            self.max_x = position.x

        if position.y > self.max_y:
            self.max_y = position.y

        assert position not in self.rooms

        self.rooms[position] = room
        self.room_list.append(room)
        self.areas[room.area].rooms.append(room)

    def add_area(self, parent: AreaInfo | None):
        id = len(self.areas)
        area = AreaInfo(
            id,
            parent=parent.id if parent is not None else None,
            depth=id,
        )
        self.areas[id] = area
        return area

    def clone(self):
        room_list = [room.clone() for room in self.room_list]
        rooms = {room.position: room for room in room_list}
        areas = {
            area.id: AreaInfo(
                area.id,
                area.parent,
                area.depth,
                rooms=[rooms[room.position] for room in area.rooms],
            )
            for area in self.areas.values()
        }

        cloned_object = copy(self)
        cloned_object.room_list = room_list
        cloned_object.rooms = rooms
        cloned_object.areas = areas
        cloned_object.required_keys = copy(self.required_keys)
        cloned_object.altars = copy(self.altars)

        return cloned_object
