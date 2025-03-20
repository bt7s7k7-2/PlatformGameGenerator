from dataclasses import dataclass, field
from math import inf
from random import Random
from time import perf_counter
from typing import Iterable

from ..game_core.Universe import Universe
from ..generation.Map import Map
from ..generation.MapGenerator import GenerationStage, MapGenerator
from ..generation.Requirements import Requirements
from ..generation.RoomController import RoomController
from ..generation.RoomInfo import RoomInfo
from ..generation.RoomParameter import UNUSED_PARAMETER, RoomParameter, RoomParameterCollection
from ..support.Point import Point
from .DifficultyReport import DifficultyReport
from .LevelSolver import LevelSolver, LevelSolverState
from .PathFinder import PathFinder


@dataclass
class LevelCandidate:
    requirements: Requirements
    _map_generator: MapGenerator | None = None
    _path_finder: PathFinder | None = None

    solution: LevelSolverState | None = None

    def get_map_generator(self):
        if self._map_generator is None:
            self._map_generator = MapGenerator(self.requirements)
        return self._map_generator

    def get_map(self):
        return self.get_map_generator().map

    def ensure_generation_stage(self, stage: GenerationStage, /, allow_greater: bool, force_clone: bool = False):
        if self.get_map_generator().stage < stage:
            updated_candidate = self.clone()
            updated_candidate.get_map_generator().generate(target_stage=stage)
            return updated_candidate
        if not allow_greater and self.get_map_generator().stage > stage:
            regressed_candidate = LevelCandidate(self.requirements)
            regressed_candidate.get_map_generator().generate(target_stage=stage)
            return regressed_candidate
        return self.clone() if force_clone else self

    def get_path_finder(self):
        if self._path_finder is None:
            self._path_finder = PathFinder(self.get_map())
        return self._path_finder

    def set_map(self, map: Map):
        self._map = map
        self.invalidate_pathfinder_cache()

    def invalidate_pathfinder_cache(self):
        self._path_finder = None

    def clone(self):
        return LevelCandidate(
            requirements=self.requirements,
            _map_generator=self._map_generator.clone() if self._map_generator else None,
            solution=self.solution,
        )


@dataclass
class DifficultyOptimizer:
    universe: Universe
    target_difficulty: RoomParameterCollection
    random: Random
    max_population: int = 10
    elitism_factor: float = 0.2
    selection_factor: float = 0.3
    default_requirements: Requirements = field(default_factory=lambda: Requirements(seed=0))

    valid_candidates: list[tuple[LevelCandidate, LevelCandidate, float]] = field(default_factory=lambda: [])

    def get_best_candidate(self):
        return self.valid_candidates[0][1]

    def get_best_fitness(self):
        return self.valid_candidates[0][2]

    def evaluate_candidates(self, candidates: list[LevelCandidate]):
        start_time = perf_counter()
        self.valid_candidates.clear()

        for candidate in candidates:
            keys_stage = candidate.ensure_generation_stage(GenerationStage.KEYS, allow_greater=True)
            solver = LevelSolver(keys_stage.get_map(), keys_stage.get_path_finder())

            if keys_stage.solution is None:
                solution = solver.solve()
                keys_stage.solution = solution

            prefabs_stage = keys_stage.ensure_generation_stage(GenerationStage.PREFABS, allow_greater=True)
            assert prefabs_stage.solution is not None
            difficulty = self.get_difficulty_along_path(prefabs_stage.get_map(), prefabs_stage.solution.get_steps_as_single_path())
            fitness = self.get_fitness(difficulty)
            self.valid_candidates.append((keys_stage, prefabs_stage, fitness))

        self.valid_candidates.sort(key=lambda v: v[2], reverse=True)
        end_time = perf_counter()

        print(f"Evaluating candidates took: {(end_time - start_time) * 1000:.2f} ms")
        print(f"Generation candidate fitness: {[x[2] for x in self.valid_candidates]}")

    def initialize_population(self):
        candidates: list[LevelCandidate] = []

        for _ in range(self.max_population):
            requirements = self.default_requirements.clone()
            requirements.seed = self.random.random()
            candidate = LevelCandidate(requirements)
            candidates.append(candidate)

        self.evaluate_candidates(candidates)

    def get_room_difficulty(self, room: RoomInfo):
        RoomController(self.universe, room=room).initialize_room(None)
        return room.difficulty

    def get_difficulty_along_path(self, map: Map, path: Iterable[Point]):
        start_time = perf_counter()

        report = DifficultyReport()
        visited_rooms = dict[Point, DifficultyReport]()
        for room_position in path:
            # Sprawl is how long the solution is, so increment it for each step of the solution
            report.increment_parameter(RoomParameter.SPRAWL, 1)

            room = map.rooms[room_position]

            if room_position in visited_rooms:
                # Do not add reward score if this room was visited already, you can't collect the gems twice
                difficulty_without_reward = RoomParameterCollection().copy_parameters_from(visited_rooms[room_position])
                difficulty_without_reward.set_parameter(RoomParameter.REWARD, 0)
                report.add_parameter_from(difficulty_without_reward)
                continue

            difficulty = self.get_room_difficulty(room)
            report.add_parameter_from(difficulty)
            visited_rooms[room_position] = difficulty

        end_time = perf_counter()

        print(f"Calculating difficulty along path took: {(end_time - start_time) * 1000:.2f} ms")
        return report

    def get_fitness(self, difficulty: DifficultyReport):
        inv_fitness = 0

        if self.target_difficulty.get_parameter(RoomParameter.ENEMY) != UNUSED_PARAMETER:
            inv_fitness += abs(self.target_difficulty.get_parameter(RoomParameter.ENEMY) - difficulty.get_parameter(RoomParameter.ENEMY))

        if self.target_difficulty.get_parameter(RoomParameter.JUMP) != UNUSED_PARAMETER:
            inv_fitness += abs(self.target_difficulty.get_parameter(RoomParameter.JUMP) - difficulty.get_parameter(RoomParameter.JUMP))

        if self.target_difficulty.get_parameter(RoomParameter.REWARD) != UNUSED_PARAMETER:
            inv_fitness += abs(self.target_difficulty.get_parameter(RoomParameter.REWARD) - difficulty.get_parameter(RoomParameter.REWARD))

        if self.target_difficulty.get_parameter(RoomParameter.SPRAWL) != UNUSED_PARAMETER:
            inv_fitness += abs(self.target_difficulty.get_parameter(RoomParameter.SPRAWL) - difficulty.get_parameter(RoomParameter.SPRAWL))

        return 1 / inv_fitness if inv_fitness != 0 else inf
