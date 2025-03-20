from copy import copy
from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain, pairwise, permutations
from time import perf_counter
from typing import Iterable, Tuple

from ..generation.Map import Map
from ..generation.RoomInfo import NO_KEY, NOT_CONNECTED
from ..support.Direction import Direction
from ..support.Point import Point
from .PathFinder import PathFinder


@dataclass
class LevelSolverState:
    position: Point
    length: float = 0
    steps: list[list[Point]] = field(default_factory=lambda: [])
    _keys: dict[int, int] = field(default_factory=lambda: {})
    unlock_state: set[Tuple[Point, Direction | None]] = field(default_factory=lambda: set())

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
        return cloned_object


@dataclass
class LevelSolver:
    map: Map

    @cached_property
    def path_finder(self):
        return PathFinder(self.map)

    @cached_property
    def key_locations(self):
        keys: dict[int, list[Point]] = {}
        for room in self.map.room_list:
            if room.pickup_type > NO_KEY:
                keys.setdefault(room.pickup_type, []).append(room.position)
        return keys

    def solve(self):
        start_time = perf_counter()
        altars = self.map.altars
        candidates: list[LevelSolverState] = []
        for altar_order in permutations(altars, len(altars)):
            print(f"-- Solving candidate {altar_order}")
            solution = self.solve_permutation(altar_order)
            print(f"-- Solution of length {solution.length} for {altar_order}")
            candidates.append(solution)

        best_candidate = min(candidates, key=lambda v: v.length)
        end_time = perf_counter()
        print(f"Best candidate length: {best_candidate.length}, took {(end_time-start_time)*100:.2f}ms")
        return best_candidate

    def solve_permutation(self, altars: Iterable[Point]):
        state = LevelSolverState(position=Point.ZERO)
        portal_position = self.map.portal
        assert portal_position is not None
        for target_position in chain(altars, [portal_position]):
            print(f"Solving path from {state.position} to {target_position}")
            self.solve_path(state, target_position)
        return state

    def solve_path(self, state: LevelSolverState, end: Point):
        checkpoint = state

        while checkpoint.position != end:
            path = self.path_finder.find_path(checkpoint.position, end, best_effort=False, can_traverse_locked_doors=True)
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

                if checkpoint.is_unlocked(path_position, direction):
                    print(f"Detected door at {path_position} -> {direction} but it is already unlocked")
                    continue

                key_to_find = connection
                print(f"Detected locked door at {path_position} -> {direction} with required key {connection}")

                if state.get_key(connection) > 0:
                    state.use_key(connection)
                    state.unlock(path_position, direction)
                    print(f"Unlocking door {path_position} -> {direction} with key from inventory")
                    continue

                possible_keys = self.key_locations[key_to_find]
                key_paths = [
                    v
                    for v in (
                        self.path_finder.find_path(
                            path_position,
                            key_position,
                            can_traverse_locked_doors=checkpoint.unlock_state,
                            best_effort=False,
                        )
                        for key_position in possible_keys
                        if not checkpoint.is_room_key_pickup_used(key_position)
                    )
                    if v is not None
                ]
                assert len(key_paths) > 0

                best_key_path = min(key_paths, key=lambda v: len(v))
                best_key = best_key_path[-1]
                print(f"Found key at {best_key}")

                path_to_key = self.path_finder.find_path(
                    checkpoint.position,
                    best_key,
                    can_traverse_locked_doors=True,
                    best_effort=False,
                )
                assert path_to_key is not None
                path_from_key = list(reversed(best_key_path))
                checkpoint.add_step(path_to_key)
                checkpoint.add_step(path_from_key)
                print(f"Unlocking door {path_position} -> {direction}")
                checkpoint.use_room_key_pickup(best_key)
                checkpoint.unlock(path_position, direction)
                print(f"Getting key adds {len(path_to_key) + len(path_from_key)}")
                break
            else:
                checkpoint.add_step(path)
                continue
