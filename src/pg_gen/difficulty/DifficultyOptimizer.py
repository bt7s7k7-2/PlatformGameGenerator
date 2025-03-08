from dataclasses import dataclass
from time import perf_counter

from ..game_core.Universe import Universe
from ..generation.MapGenerator import MapGenerator
from ..generation.RoomController import RoomController
from ..generation.RoomInfo import RoomInfo
from .DifficultyReport import DifficultyReport


@dataclass
class DifficultyOptimizer:
    universe: Universe
    map: MapGenerator

    def get_room_difficulty(self, room: RoomInfo):
        RoomController(self.universe, room=room).initialize_room(None)
        return room.difficulty

    def get_global_difficulty(self):
        start = perf_counter()

        report = DifficultyReport()

        for room in self.map.room_list:
            difficulty = self.get_room_difficulty(room)
            report.add_parameter_from(difficulty)

        end = perf_counter()

        print(f"Calculating global difficulty took: {(end - start) * 100:.2f} ms")

        return report
