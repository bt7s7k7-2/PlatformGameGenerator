from copy import copy
from dataclasses import dataclass, field

from .RoomParameter import RoomParameterCollection


@dataclass
class Requirements:
    seed: float
    max_rooms: int = 50
    max_width: int = 25
    max_height: int = 25
    sprawl_chance: float = 0.5
    lock_chance: float = 0.75
    max_rooms_per_area: int = 6
    min_rooms_per_area: int = 3
    start_area_size: int = 5
    altar_count: int = 3
    parameter_chances: RoomParameterCollection = field(default_factory=lambda: RoomParameterCollection().set_all_parameters(0.75))

    def clone(self):
        cloned_object = copy(self)
        cloned_object.parameter_chances = RoomParameterCollection().copy_parameters_from(self.parameter_chances)
        return cloned_object
