from random import Random
from time import perf_counter

from ..support.keys import KEY_COLORS
from ..support.Point import Point
from .AreaInfo import AreaInfo
from .Map import Map
from .Requirements import Requirements
from .RoomInfo import ALTAR, NO_KEY, NOT_CONNECTED, PORTAL, RoomInfo
from .RoomParameter import RoomParameter
from .RoomPrefabRegistry import RoomPrefabRegistry

_POSSIBLE_KEYS = [i + 1 for i in range(len(KEY_COLORS))]


class MapGenerator:
    requirements: Requirements
    pending_rooms: list[RoomInfo]
    current_room: RoomInfo
    map: Map
    random_source: Random
    pending_rooms: list[RoomInfo]

    def __init__(self, requirements: Requirements):
        super().__init__()
        self.requirements = requirements
        self.random_source = Random(requirements.seed)
        self.pending_rooms = []

        self.map = Map()
        root_area = self.map.add_area(None)
        root_room = self.create_room(Point.ZERO, root_area)
        assert root_room is not None
        self.pending_rooms.append(root_room)
        self.current_room = root_room

    def clone(self):
        cloned_object = MapGenerator(self.requirements)
        cloned_object.random_source.setstate(self.random_source.getstate())
        return cloned_object

    def create_room(self, position: Point, area: AreaInfo):
        map = self.map

        if position.x < map.min_x:
            if self.requirements.max_width is not None:
                new_width = map.max_x - map.min_x + 2
                if new_width > self.requirements.max_width:
                    return None

        if position.y < map.min_y:
            if self.requirements.max_height is not None:
                new_height = map.max_y - map.min_y + 2
                if new_height > self.requirements.max_height:
                    return None

        if position.x > map.max_x:
            if self.requirements.max_width is not None:
                new_width = map.max_x - map.min_x + 2
                if new_width > self.requirements.max_width:
                    return None

        if position.y > map.max_y:
            if self.requirements.max_height is not None:
                new_height = map.max_y - map.min_y + 2
                if new_height > self.requirements.max_height:
                    return None

        room = RoomInfo(self.random_source.random(), position, area.id)
        room.copy_parameters_from(self.requirements.parameter_chances)

        map.add_room(room)

        print(f"Added room at {position}, current size is now {len(map.rooms)} at {map.max_x - map.min_x + 1} x {map.max_y - map.min_y + 1}")

        return room

    def next_iteration(self):
        if len(self.map.rooms) >= self.requirements.max_rooms:
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
            if self.map.has_room(next_position):
                connected_room = self.map.get_room(next_position)

                compatible = connected_room.area == self.current_room.area
                if not compatible:
                    continue

                self.current_room.set_connection(direction, 0)
                connected_room.set_connection(direction.invert(), 0)
                self.current_room = connected_room
                success = True
                break

            current_area = self.map.areas[self.current_room.area]
            rooms_in_current_area = len(current_area.rooms)
            next_area = current_area
            required_key = NO_KEY

            max_rooms = self.requirements.start_area_size if current_area.id == 0 else self.requirements.max_rooms_per_area
            min_rooms = self.requirements.start_area_size if current_area.id == 0 else self.requirements.min_rooms_per_area

            if rooms_in_current_area >= max_rooms or (rooms_in_current_area > min_rooms and self.random_source.random() < self.requirements.lock_chance):
                required_key = self.random_source.choice(_POSSIBLE_KEYS)
                next_area = self.map.add_area(parent=current_area)

            new_room = self.create_room(next_position, next_area)
            if new_room is None:
                continue

            self.current_room.set_connection(direction, required_key)
            new_room.set_connection(direction.invert(), NO_KEY)

            if required_key != NO_KEY:
                self.map.add_key_requirement(current_area.depth, required_key)

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
        if self.random_source.random() < self.requirements.sprawl_chance:
            self.current_room = self.random_source.choice(self.pending_rooms)
            return True

        return True

    def generate_layout(self):
        while True:
            success = self.next_iteration()
            if not success:
                break

    def generate(self):
        start = perf_counter()
        self.generate_layout()
        self.distribute_keys()
        self.assign_room_prefabs()
        end = perf_counter()

        print(f"Map generation took: {(end - start) * 1000:.2f} ms")

        return self.map

    def distribute_keys(self):
        map = self.map

        map.required_keys.sort(key=lambda x: x[0])
        rooms_by_depth: dict[int, list[RoomInfo]] = {}

        for altar in map.altars:
            room = map.rooms[altar]
            room.pickup_type = ALTAR

        if map.portal is not None:
            room = map.rooms[map.portal]
            room.pickup_type = PORTAL

        for max_depth, key in map.required_keys:
            fail_count = 0

            while True:
                if max_depth in rooms_by_depth:
                    possible_rooms = rooms_by_depth[max_depth]
                else:
                    possible_rooms = [v for v in map.room_list if map.areas[v.area].depth == max_depth]
                    rooms_by_depth[max_depth] = possible_rooms
                    print(f"Keys for depth {max_depth}: {[room.area for room in possible_rooms]}")

                if len(possible_rooms) == 0:
                    if max_depth == 0:
                        print(f"Cannot find place for key {key} at {max_depth}")
                        break
                    max_depth -= 1
                    continue

                room = self.random_source.choice(possible_rooms)
                if room.pickup_type != NO_KEY:
                    print(f"Cannot use {key} at {room.area}")
                    possible_rooms.remove(room)
                    continue

                if fail_count < 10 and room.uses_key_of_type(key):
                    fail_count += 1
                    continue

                room.pickup_type = key
                possible_rooms.remove(room)
                print(f"Saved key {key} at {room.area}")
                break

    def assign_room_prefabs(self):
        start = perf_counter()
        map = self.map

        for room in map.room_list:
            debug: list[str] = []

            is_root = room.position == Point.ZERO
            if is_root:
                room.set_parameter(RoomParameter.ENEMY, 0)

            group = "default"

            if is_root:
                group = "starter"

            if room.pickup_type == ALTAR:
                group = "altar"

            if room.pickup_type == PORTAL:
                group = "portal"

            prefabs = RoomPrefabRegistry.find_rooms(
                group,
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
        end = perf_counter()

        print(f"Assigning room prefabs took: {(end - start) * 1000:.2f} ms")
