from dataclasses import dataclass, field
from functools import cached_property
from random import Random
from typing import Tuple

from ..support.keys import KEY_COLORS
from ..support.Point import Point
from .RoomInfo import NO_KEY, NOT_CONNECTED, RoomInfo
from .RoomParameter import RoomParameter, RoomParameterCollection
from .RoomPrefabRegistry import RoomPrefabRegistry


@dataclass
class AreaInfo:
    id: int
    parent: int | None
    depth: int
    children: list[int] = field(default_factory=lambda: [])
    rooms: list[RoomInfo] = field(default_factory=lambda: [])


_POSSIBLE_KEYS = [i + 1 for i in range(len(KEY_COLORS))]


@dataclass(kw_only=True)
class MapGenerator(RoomParameterCollection):
    seed: int
    max_rooms: int = 10
    max_width: int | None = None
    max_height: int | None = None
    sprawl_chance: float = 0.5
    lock_chance: float = 0.75
    key_chance: float = 0.5
    max_rooms_per_area: int = 6
    min_rooms_per_area: int = 3
    start_area_size = 5

    _min_x = 0
    _min_y = 0
    _max_x = 0
    _max_y = 0

    room_list: list[RoomInfo] = field(default_factory=lambda: [])
    rooms: dict[Point, RoomInfo] = field(default_factory=lambda: {})
    areas: dict[int, AreaInfo] = field(default_factory=lambda: {})
    pending_rooms: list[RoomInfo] = field(default_factory=lambda: [])
    current_room: RoomInfo = None  # type: ignore
    current_area: AreaInfo = None  # type: ignore

    required_keys: list[Tuple[int, int]] = field(default_factory=lambda: [])

    def add_key_requirement(self, max_depth: int, key: int):
        self.required_keys.append((max_depth, key))

    @cached_property
    def random_source(self):
        return Random(self.seed)

    def get_start(self):
        return Point(self._min_x, self._min_y)

    def get_size(self):
        return Point(self._max_x - self._min_x, self._max_y - self._min_y)

    def has_room(self, position: Point):
        return position in self.rooms

    def get_room(self, position: Point):
        return self.rooms[position]

    def get_rooms(self):
        return iter(self.rooms.values())

    def add_room(self, position: Point, area: AreaInfo):
        if position.x < self._min_x:
            if self.max_width is not None:
                new_width = self._max_x - self._min_x + 2
                if new_width > self.max_width:
                    return None
            self._min_x = position.x

        if position.y < self._min_y:
            if self.max_height is not None:
                new_height = self._max_y - self._min_y + 2
                if new_height > self.max_height:
                    return None
            self._min_y = position.y

        if position.x > self._max_x:
            if self.max_width is not None:
                new_width = self._max_x - self._min_x + 2
                if new_width > self.max_width:
                    return None
            self._max_x = position.x

        if position.y > self._max_y:
            if self.max_height is not None:
                new_height = self._max_y - self._min_y + 2
                if new_height > self.max_height:
                    return None
            self._max_y = position.y

        room = RoomInfo(self.random_source.random(), position, area.id)
        room.copy_parameters(self)
        assert position not in self.rooms
        self.rooms[position] = room
        self.room_list.append(room)
        area.rooms.append(room)

        print(f"Added room at {position}, current size is now {len(self.rooms)} at {self._max_x - self._min_x + 1} x {self._max_y - self._min_y + 1}")

        return room

    def add_area(self, parent: AreaInfo | None):
        id = len(self.areas)
        area = AreaInfo(
            id,
            parent=parent.id if parent is not None else None,
            depth=id,  # parent.depth + 1 if parent is not None else 0,
        )
        self.areas[id] = area
        return area

    def next_iteration(self):
        if len(self.rooms) >= self.max_rooms:
            return False

        directions = self.current_room.directions
        success = False

        while len(directions) > 0:
            directionIndex = self.random_source.randint(0, len(directions) - 1)
            direction = directions.pop(directionIndex)

            already_connected = self.current_room.get_connection(direction) != NOT_CONNECTED
            if already_connected:
                continue

            next_position = self.current_room.position + Point.from_direction(direction)
            if self.has_room(next_position):
                connected_room = self.get_room(next_position)

                compatible = connected_room.area == self.current_room.area
                if not compatible:
                    continue

                self.current_room.set_connection(direction, 0)
                connected_room.set_connection(direction.invert(), 0)
                self.current_room = connected_room
                success = True
                break

            current_area = self.areas[self.current_room.area]
            rooms_in_current_area = len(current_area.rooms)
            next_area = current_area
            required_key = NO_KEY

            max_rooms = self.start_area_size if current_area.id == 0 else self.max_rooms_per_area
            min_rooms = self.start_area_size if current_area.id == 0 else self.min_rooms_per_area

            if rooms_in_current_area >= max_rooms or (rooms_in_current_area > min_rooms and self.random_source.random() < self.lock_chance):
                required_key = self.random_source.choice(_POSSIBLE_KEYS)
                next_area = self.add_area(parent=current_area)

            new_room = self.add_room(next_position, next_area)
            if new_room is None:
                continue

            self.current_room.set_connection(direction, required_key)
            new_room.set_connection(direction.invert(), NO_KEY)

            if required_key != NO_KEY:
                self.add_key_requirement(current_area.depth, required_key)

            self.current_room = new_room
            self.pending_rooms.append(self.current_room)
            success = True
            break

        # If we are not successful in any direction, remove this room from pending rooms and switch to a random other room
        if not success:
            self.pending_rooms.remove(self.current_room)
            if len(self.pending_rooms) == 0:
                return False
            self.current_room = self.random_source.choice(self.pending_rooms)
            return True

        # Random chance to switch to a different branch
        if self.random_source.random() < self.sprawl_chance:
            self.current_room = self.random_source.choice(self.pending_rooms)
            return True

        return True

    def generate(self):
        root_room = self.add_room(Point.ZERO, self.add_area(None))
        assert root_room is not None
        self.pending_rooms.append(root_room)
        self.current_room = root_room

        while True:
            success = self.next_iteration()
            if not success:
                break

        self.required_keys.sort(key=lambda x: x[0])
        rooms_by_depth: dict[int, list[RoomInfo]] = {}
        for max_depth, key in self.required_keys:
            fail_count = 0

            while True:
                if max_depth in rooms_by_depth:
                    possible_rooms = rooms_by_depth[max_depth]
                else:
                    possible_rooms = [v for v in self.room_list if self.areas[v.area].depth == max_depth]
                    rooms_by_depth[max_depth] = possible_rooms
                    print(f"Keys for depth {max_depth}: {[room.area for room in possible_rooms]}")

                if len(possible_rooms) == 0:
                    if max_depth == 0:
                        print(f"Cannot find place for key {key} at {max_depth}")
                        break
                    max_depth -= 1
                    continue

                room = self.random_source.choice(possible_rooms)
                if room.provides_key != NO_KEY:
                    print(f"Cannot use {key} at {room.area}")
                    possible_rooms.remove(room)
                    continue

                if fail_count < 10 and room.uses_key_of_type(key):
                    fail_count += 1
                    continue

                room.provides_key = key
                possible_rooms.remove(room)
                print(f"Saved key {key} at {room.area}")
                break

    def assign_room_prefabs(self):
        for room in self.room_list:
            debug: list[str] = []

            is_root = room.position == Point.ZERO
            if is_root:
                room.set_parameter(RoomParameter.ENEMY, 0)

            prefabs = RoomPrefabRegistry.find_rooms(
                "starter" if is_root else "default",
                requirements=room,
                context=None,
                debug_info=debug,
            )

            if len(prefabs) == 0:
                print(f"Failed to find prefab for room {room}")
                print("\n".join(debug))
                room.prefab = RoomPrefabRegistry.rooms_by_group["fallback"][0]
                continue

            room.prefab = self.random_source.choice(prefabs)
