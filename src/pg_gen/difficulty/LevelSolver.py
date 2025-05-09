from copy import copy
from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain, pairwise
from time import perf_counter

from ..generation.Map import Map
from ..generation.RoomInfo import NO_KEY, NOT_CONNECTED
from ..support.Direction import Direction
from ..support.keys import KEY_COLORS
from ..support.Point import Point
from .PathFinder import PathFinder


@dataclass
class LevelSolverState:
    position: Point
    length: float = 0
    steps: list[list[Point]] = field(default_factory=lambda: [])
    _keys: dict[int, int] = field(default_factory=lambda: {})
    unlock_state: set[tuple[Point, Direction | None]] = field(default_factory=lambda: set())

    def get_steps_as_single_path(self):
        previous: Point | None = None
        for path in self.steps:
            for room in path:
                if room == previous:
                    continue
                yield room
                previous = room

    def add_step(self, path: list[Point]):
        assert path[0] == self.position

        if len(path) == 1:
            return

        self.steps.append(path)
        # Path also includes the starting position, so its length is one longer than the amount of steps required to perform it
        self.length += len(path) - 1
        self.position = path[-1]

    def is_unlocked(self, room: Point, direction: Direction):
        return (room, direction) in self.unlock_state

    def is_room_key_pickup_used(self, room: Point):
        return (room, None) in self.unlock_state

    def unlock(self, room: Point, direction: Direction):
        self.unlock_state.add((room, direction))

    def use_room_key_pickup(self, room: Point):
        self.unlock_state.add((room, None))

    def get_key(self, key: int):
        return self._keys.get(key, 0)

    def modify_key(self, key: int, change: int):
        value = self.get_key(key) + change
        if value == 0:
            del self._keys[key]
        else:
            self._keys[key] = value

    def pickup_key(self, key: int):
        self.modify_key(key, 1)

    def use_key(self, key: int):
        self.modify_key(key, -1)

    def clone(self):
        cloned_object = copy(self)
        cloned_object._keys = copy(self._keys)
        cloned_object.unlock_state = copy(self.unlock_state)
        cloned_object.steps = copy(self.steps)
        return cloned_object


@dataclass
class LevelSolver:
    map: Map
    path_finder: PathFinder

    @cached_property
    def key_locations(self):
        keys: dict[int, list[Point]] = {}
        for key_type in range(len(KEY_COLORS)):
            keys[key_type + 1] = []

        for room in self.map.room_list:
            if room.pickup_type > NO_KEY:
                keys[room.pickup_type].append(room.position)

        return keys

    def solve(self):
        start_time = perf_counter()
        altars = self.map.altars
        portal = self.map.portal
        assert portal is not None
        initial_state = LevelSolverState(position=self.map.room_list[0].position)
        solutions: list[LevelSolverState] = []
        self.solve_permutation(initial_state, altars, portal, solutions)
        if len(solutions) == 0:
            return None

        best_candidate = solutions[0]
        end_time = perf_counter()
        print(f"Best candidate length: {best_candidate.length}, took {(end_time-start_time)*100:.2f}ms")
        return best_candidate

    def solve_permutation(self, state: LevelSolverState, remaining_altars: list[Point], portal: Point, solutions: list[LevelSolverState]):
        for target in remaining_altars if len(remaining_altars) > 0 else [portal]:
            checkpoint = state.clone()
            checkpoint = self.solve_path(checkpoint, target)
            if checkpoint is None:
                continue

            if len(solutions) > 0 and solutions[0].length <= checkpoint.length:
                continue

            if target == portal:
                print(f"-- Solution of length {checkpoint.length}")
                if len(solutions) == 0:
                    solutions.append(checkpoint)
                else:
                    solutions[0] = checkpoint
                return

            child_remaining_altars = remaining_altars[:]
            child_remaining_altars.remove(target)

            self.solve_permutation(checkpoint, child_remaining_altars, portal, solutions)

    def solve_path(self, state: LevelSolverState, end: Point, circular_dependency_prevention: set[int] | None = None):
        while state.position != end:
            path = self.path_finder.find_path(state.position, end, best_effort=False, can_traverse_locked_doors=True)
            assert path is not None

            for path_position, next in pairwise(path):
                room = self.map.rooms[path_position]

                if room.pickup_type > NO_KEY and not state.is_room_key_pickup_used(path_position):
                    print(f"Pick up key {room.pickup_type} at {path_position}")
                    state.use_room_key_pickup(path_position)
                    state.pickup_key(room.pickup_type)

                vector = next - path_position
                direction = vector.as_direction()

                connection = room.get_connection(direction)
                assert connection != NOT_CONNECTED
                if connection == NO_KEY:
                    continue

                if state.is_unlocked(path_position, direction):
                    print(f"Detected door at {path_position} -> {direction} but it is already unlocked")
                    continue

                key_to_find = connection
                print(f"Detected locked door at {path_position} -> {direction} with required key {connection}")

                if circular_dependency_prevention and key_to_find in circular_dependency_prevention:
                    return None

                if state.get_key(connection) > 0:
                    state.use_key(connection)
                    state.unlock(path_position, direction)
                    print(f"Unlocking door {path_position} -> {direction} with key from inventory")
                    continue

                possible_keys = [x for x in self.key_locations[key_to_find] if not state.is_room_key_pickup_used(x)]
                key_acquisition_candidates: list[LevelSolverState] = []

                forbidden_keys = set(chain(circular_dependency_prevention, [key_to_find]) if circular_dependency_prevention else [key_to_find])
                for key_position in possible_keys:
                    checkpoint = state.clone()
                    checkpoint = self.solve_path(checkpoint, key_position, circular_dependency_prevention=forbidden_keys)
                    if checkpoint is None:
                        continue
                    checkpoint = self.solve_path(checkpoint, path_position)
                    if checkpoint is None:
                        continue

                    key_acquisition_candidates.append(checkpoint)

                if len(key_acquisition_candidates) == 0:
                    return None

                best_key_path = min(key_acquisition_candidates, key=lambda v: v.length)
                best_key = best_key_path.position
                print(f"Found key at {best_key}")

                print(f"Unlocking door {path_position} -> {direction}")
                state.use_room_key_pickup(best_key)
                state.unlock(path_position, direction)
                print(f"Getting key adds {best_key_path.length - state.length}")
                state = best_key_path
                break
            else:
                state.add_step(path)
                continue

        return state
