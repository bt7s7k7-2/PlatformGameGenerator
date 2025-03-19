from copy import copy
from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain, permutations
from typing import Iterable

from ..generation.Map import Map
from ..generation.RoomInfo import NO_KEY
from ..support.Point import Point
from .PathFinder import PathFinder


@dataclass
class LevelSolverState:
    position: Point
    length: float = 0
    steps: list[list[Point]] = field(default_factory=lambda: [])
    _keys: dict[int, int] = field(default_factory=lambda: {})

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
        altars = self.map.altars
        candidates: list[LevelSolverState] = []
        for altar_order in permutations(altars, len(altars)):
            solution = self.solve_permutation(altar_order)
            print(f"Solution of length {solution.length} for {altar_order}")
            candidates.append(solution)

        best_candidate = min(candidates, key=lambda v: v.length)
        print(f"Best candidate length: {best_candidate.length}")
        return best_candidate

    def solve_permutation(self, altars: Iterable[Point]):
        state = LevelSolverState(position=Point.ZERO)
        portal_position = self.map.portal
        assert portal_position is not None
        for target_position in chain(altars, [portal_position]):
            path = self.path_finder.find_path(state.position, target_position)
            state.steps.append(path)
            state.length += len(path) - 1  # Path also includes the starting position, so its length is one longer than the amount of steps required to perform it
            state.position = target_position
        return state
