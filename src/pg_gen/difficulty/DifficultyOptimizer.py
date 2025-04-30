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
from ..support.support import weighted_random
from .DifficultyReport import DifficultyReport
from .LevelSolver import LevelSolver, LevelSolverState
from .PathFinder import PathFinder


@dataclass
class ParameterInfo:
    name: str | RoomParameter
    is_float: bool
    range: tuple[float, float]
    weight: float

    @property
    def min(self):
        return self.range[0]

    @property
    def max(self):
        return self.range[1]

    def set(self, target: Requirements, value: float):
        if isinstance(self.name, RoomParameter):
            target.parameter_chances.set_parameter(self.name, value)
            return

        setattr(target, self.name, value)

    def get(self, target: Requirements):
        if isinstance(self.name, RoomParameter):
            return target.parameter_chances.get_parameter(self.name)

        return getattr(target, self.name)

    def override_value(self, value: float):
        self.range = (value, value)
        self.weight = 0


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

    def ensure_generation_stage(self, stage: GenerationStage, /, allow_greater: bool, force_clone: bool = False, override_seed: float | None = None):
        if self.get_map_generator().stage < stage:
            updated_candidate = self.clone()

            if override_seed is not None:
                updated_candidate.get_map_generator().random = Random(override_seed)

            updated_candidate.get_map_generator().generate(target_stage=stage)
            return updated_candidate
        if not allow_greater and self.get_map_generator().stage > stage:
            regressed_candidate = LevelCandidate(self.requirements)
            map_generator = regressed_candidate.get_map_generator()
            if override_seed:
                map_generator.generate(target_stage=GenerationStage(stage.value - 1))
                map_generator.random = Random(override_seed)
                map_generator.generate(target_stage=stage)
            else:
                map_generator.generate(target_stage=stage)
            return regressed_candidate

        assert override_seed is None
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
    max_generations: int = 5

    parameters: list[ParameterInfo] = field(
        default_factory=lambda: [
            ParameterInfo("seed", is_float=True, range=(0, 1), weight=0.1),
            ParameterInfo("max_rooms", is_float=False, range=(10, 100), weight=0.75),
            ParameterInfo("max_width", is_float=False, range=(10, 30), weight=0.5),
            ParameterInfo("max_height", is_float=False, range=(10, 25), weight=0.5),
            # ParameterInfo("sprawl_chance", is_float=True, range=(0.25, 0.75), weight=0.25),
            # ParameterInfo("lock_chance", is_float=True, range=(0.6, 0.8), weight=0.25),
            ParameterInfo("altar_count", is_float=False, range=(0, 3), weight=0.5),
            ParameterInfo(RoomParameter.ENEMY, is_float=True, range=(0, 1), weight=1.5),
            ParameterInfo(RoomParameter.JUMP, is_float=True, range=(0, 1), weight=1.5),
            ParameterInfo(RoomParameter.REWARD, is_float=True, range=(0, 1), weight=1.5),
        ]
    )

    valid_candidates: list[tuple[LevelCandidate, LevelCandidate, float, DifficultyReport]] = field(default_factory=lambda: [])

    def _apply_random_parameters(self, target: Requirements):
        for parameter in self.parameters:
            value = self.random.uniform(parameter.min, parameter.max) if parameter.is_float else self.random.randint(int(parameter.min), int(parameter.max))
            parameter.set(target, value)

    def _mutate_random_parameter(self, target: Requirements):
        parameter = weighted_random(self.parameters, self.random.random(), lambda v: v.weight)
        value = parameter.get(target)
        range = (parameter.max - parameter.min) * 0.25
        delta = self.random.uniform(-range, range)
        value += delta

        if value > parameter.max:
            value = parameter.max
        elif value < parameter.min:
            value = parameter.min

        if not parameter.is_float:
            value = int(value)

        parameter.set(target, value)

    def _crossover_parameters(self, a: Requirements, b: Requirements):
        result = Requirements(seed=0)
        for parameter in self.parameters:
            source = a if self.random.random() > 0.5 else b
            parameter.set(result, parameter.get(source))
        return result

    def get_parameter(self, name: str | RoomParameter):
        return next(v for v in self.parameters if v.name == name)

    def get_best_candidate(self):
        return self.valid_candidates[0][1]

    def get_best_fitness(self):
        return self.valid_candidates[0][2]

    def get_best_difficulty(self):
        return self.valid_candidates[0][3]

    def evaluate_candidates(self, candidates: list[LevelCandidate]):
        start_time = perf_counter()
        self.valid_candidates.clear()

        for candidate in candidates:
            keys_stage = candidate.ensure_generation_stage(GenerationStage.KEYS, allow_greater=True)
            solver = LevelSolver(keys_stage.get_map(), keys_stage.get_path_finder())

            if keys_stage.solution is None:
                solution = solver.solve()
                if solution is None:
                    continue

                keys_stage.solution = solution

            prefabs_stage = keys_stage.ensure_generation_stage(GenerationStage.PREFABS, allow_greater=True)
            assert prefabs_stage.solution is not None
            difficulty = self.get_difficulty_along_path(prefabs_stage.get_map(), prefabs_stage.solution.get_steps_as_single_path())
            fitness = self.get_fitness(difficulty)
            self.valid_candidates.append((keys_stage, prefabs_stage, fitness, difficulty))

        self.valid_candidates.sort(key=lambda v: v[2], reverse=True)
        end_time = perf_counter()

        print(f"Evaluating candidates took: {(end_time - start_time) * 1000:.2f} ms")
        print(f"Generation candidate fitness: {[x[2] for x in self.valid_candidates]}")

    def initialize_population(self):
        candidates: list[LevelCandidate] = []

        for _ in range(self.max_population):
            requirements = Requirements(seed=0)
            self._apply_random_parameters(requirements)
            candidate = LevelCandidate(requirements)
            candidates.append(candidate)

        self.evaluate_candidates(candidates)

    def optimize(self):
        last_best_fitness = 0
        termination_trigger = 0
        for _ in range(self.max_generations):
            new_candidates: list[LevelCandidate] = []

            elitism_candidates = self.valid_candidates[0 : int(len(self.valid_candidates) * self.elitism_factor)]
            new_candidates.extend(candidate[1] for candidate in elitism_candidates)

            selection_candidates = self.valid_candidates[0 : int(len(self.valid_candidates) * self.selection_factor)]
            while len(new_candidates) < self.max_population:
                if self.random.random() < 0.3:
                    before_altars = self.random.choice(selection_candidates)[0]
                    new_candidate = before_altars.ensure_generation_stage(GenerationStage.ALTARS, allow_greater=False, override_seed=self.random.random())
                    new_candidates.append(new_candidate)
                    continue

                parent_a = self.random.choice(selection_candidates)

                if self.random.random() < 0.5:
                    new_candidate_requirements = parent_a[0].requirements.clone()
                else:
                    parent_b = parent_a
                    while parent_a == parent_b:
                        parent_b = self.random.choice(selection_candidates)

                    new_candidate_requirements = self._crossover_parameters(parent_a[0].requirements, parent_b[0].requirements)

                self._mutate_random_parameter(new_candidate_requirements)
                new_candidate = LevelCandidate(new_candidate_requirements)
                new_candidates.append(new_candidate)

            self.evaluate_candidates(new_candidates)

            best_fitness = self.get_best_fitness()
            if best_fitness == last_best_fitness:
                termination_trigger += 1
                # if termination_trigger >= 3:
                #    break
            else:
                termination_trigger = 0
                last_best_fitness = best_fitness

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
            inv_fitness += abs(self.target_difficulty.get_parameter(RoomParameter.ENEMY) - difficulty.get_parameter(RoomParameter.ENEMY)) * 0.5

        if self.target_difficulty.get_parameter(RoomParameter.JUMP) != UNUSED_PARAMETER:
            inv_fitness += abs(self.target_difficulty.get_parameter(RoomParameter.JUMP) - difficulty.get_parameter(RoomParameter.JUMP)) * 0.75

        if self.target_difficulty.get_parameter(RoomParameter.REWARD) != UNUSED_PARAMETER:
            inv_fitness += abs(self.target_difficulty.get_parameter(RoomParameter.REWARD) - difficulty.get_parameter(RoomParameter.REWARD)) * 0.1

        if self.target_difficulty.get_parameter(RoomParameter.SPRAWL) != UNUSED_PARAMETER:
            inv_fitness += abs(self.target_difficulty.get_parameter(RoomParameter.SPRAWL) - difficulty.get_parameter(RoomParameter.SPRAWL)) * 0.75

        return 1 / inv_fitness if inv_fitness != 0 else inf
