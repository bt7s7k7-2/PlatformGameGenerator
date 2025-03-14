from dataclasses import dataclass
from time import perf_counter

from ..game_core.Universe import Universe
from ..generation.Map import Map
from ..generation.MapGenerator import MapGenerator
from ..generation.Requirements import Requirements
from ..generation.RoomController import RoomController
from ..generation.RoomInfo import RoomInfo
from .DifficultyReport import DifficultyReport


@dataclass
class DifficultyOptimizer:
    universe: Universe
    requirements: Requirements

    def achieve_target_difficulty(self):
        best_map: Map | None = None
        max_attempts = 100

        while True:
            generator = MapGenerator(self.requirements)
            map = generator.generate()
            difficulty = self.get_global_difficulty(map)
            print(f"Candidate difficulty: {difficulty}")

            difficulty_matches_requirements = True
            if difficulty_matches_requirements:
                best_map = map
                return map

            max_attempts -= 1
            if max_attempts == 0:
                break

        if best_map is None:
            raise Exception("Somehow did not assign best map")

        return best_map

    def get_room_difficulty(self, room: RoomInfo):
        RoomController(self.universe, room=room).initialize_room(None)
        return room.difficulty

    def get_global_difficulty(self, map: Map):
        start = perf_counter()

        report = DifficultyReport()

        for room in map.room_list:
            difficulty = self.get_room_difficulty(room)
            report.add_parameter_from(difficulty)

        end = perf_counter()

        print(f"Calculating global difficulty took: {(end - start) * 100:.2f} ms")

        return report
