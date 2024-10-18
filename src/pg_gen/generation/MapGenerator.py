from dataclasses import dataclass, field
from random import Random
from typing import Dict, List

from ..support.Direction import Direction
from ..support.keys import KEY_COLORS, MAX_KEY_TYPE
from ..support.Point import Point
from .RoomInfo import NO_KEY, NOT_CONNECTED, RoomInfo
from .RoomPrefabRegistry import RoomPrefabRegistry


class ProgressionMarker:
    def __init__(self, key_state: Dict[int, int] = {}) -> None:
        self._key_state = key_state

    """ def create_child(self, key: int):
        child = ProgressionMarker(self._key_state.copy())
        child.increment_key(key)
        return child """

    def increment_key(self, key: int):
        if key in self._key_state:
            self._key_state[key] += 1
        else:
            self._key_state[key] = 1

    def decrement_key(self, key: int):
        assert key in self._key_state
        self._key_state[key] -= 1
        if self._key_state[key] == 0:
            self._key_state.pop(key)

    def has_key(self, key: int):
        # self._key_state dict will only have values larger than zero,
        # so if a value is present it is non-zero
        return key in self._key_state

    def __repr__(self):
        return repr(self._key_state)

    def __eq__(self, value: object):
        if isinstance(value, ProgressionMarker):
            return value._key_state == self._key_state
        return False


@dataclass(kw_only=True)
class MapGenerator:
    room_prefabs: RoomPrefabRegistry
    max_rooms: int = 10
    max_width: int | None = None
    max_height: int | None = None
    sprawl_chance: float = 0.5
    lock_chance: float = 0.75
    key_chance: float = 0.5

    _min_x = 0
    _min_y = 0
    _max_x = 0
    _max_y = 0

    _rooms: Dict[Point, RoomInfo] = field(default_factory=lambda: {}, init=False)

    def get_start(self):
        return Point(self._min_x, self._min_y)

    def get_size(self):
        return Point(self._max_x - self._min_x, self._max_y - self._min_y)

    def has_room(self, position: Point):
        return position in self._rooms

    def get_room(self, position: Point):
        return self._rooms[position]

    def get_rooms(self):
        return iter(self._rooms.values())

    def generate(self, seed: int):
        random_source = Random(seed)
        pending_rooms: List[RoomInfo] = []

        def add_room(position: Point, area: int):
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

            room = RoomInfo(random_source.random(), position, area)
            assert position not in self._rooms
            self._rooms[position] = room

            print(f"Added room at {position}, current size is now {len(self._rooms)} at {self._max_x - self._min_x + 1} x {self._max_y - self._min_y + 1}")

            return room

        root_room = add_room(Point.ZERO, 0)
        assert root_room is not None
        pending_rooms.append(root_room)

        next_area = 1
        progression = ProgressionMarker()

        while len(pending_rooms) > 0 and len(self._rooms) < self.max_rooms:
            curr_room = random_source.choice(pending_rooms)
            while len(self._rooms) < self.max_rooms:
                directions = Direction.get_directions()
                success = False
                hit_existing_room = False

                while len(directions) > 0:
                    directionIndex = random_source.randint(0, len(directions) - 1)
                    direction = directions[directionIndex]
                    directions.pop(directionIndex)

                    already_connected = curr_room.get_connection(direction) != NOT_CONNECTED
                    if already_connected:
                        continue

                    next_position = curr_room.position + Point.from_direction(direction)
                    if self.has_room(next_position):
                        connected_room = self.get_room(next_position)

                        compatible = connected_room.area == curr_room.area
                        if not compatible:
                            continue

                        curr_room.set_connection(direction, 0)
                        connected_room.set_connection(direction.invert(), 0)
                        curr_room = connected_room
                        hit_existing_room = True
                        break

                    area = curr_room.area
                    required_key = NO_KEY

                    if random_source.random() < self.lock_chance:
                        possible_keys = [i + 1 for i in range(len(KEY_COLORS))]
                        while len(possible_keys) > 0:
                            index = random_source.randint(0, len(possible_keys) - 1)
                            required_key = possible_keys.pop(index)

                            if progression.has_key(required_key):
                                progression.decrement_key(required_key)
                                area = next_area
                                next_area += 1
                                break

                            required_key = NO_KEY

                    new_room = add_room(next_position, area)
                    if new_room is None:
                        continue

                    curr_room.set_connection(direction, required_key)
                    new_room.set_connection(direction.invert(), NO_KEY)

                    if random_source.random() < self.key_chance:
                        required_key = random_source.randint(1, MAX_KEY_TYPE)
                        progression.increment_key(required_key)
                        new_room.provides_key = required_key

                    curr_room = new_room
                    success = True
                    pending_rooms.append(curr_room)
                    break

                if hit_existing_room:
                    break

                if not success:
                    room_index = pending_rooms.index(curr_room)
                    pending_rooms.pop(room_index)
                    break

                # Random chance to switch to a different branch
                if random_source.random() < self.sprawl_chance:
                    break

        for room in self._rooms.values():
            debug: list[str] = []
            prefabs = self.room_prefabs.find_rooms("default", requirements=room, debug_info=debug)
            if len(prefabs) == 0:
                print(f"Failed to find prefab for room {room}")
                print("\n".join(debug))
                room.prefab = self.room_prefabs.rooms_by_group["fallback"][0]
                continue
            room.prefab = random_source.choice(prefabs)
