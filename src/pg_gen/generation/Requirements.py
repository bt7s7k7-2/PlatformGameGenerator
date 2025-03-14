from dataclasses import dataclass, field

from .RoomParameter import RoomParameterCollection


@dataclass
class Requirements:
    seed: int
    max_rooms: int = 10
    max_width: int | None = None
    max_height: int | None = None
    sprawl_chance: float = 0.5
    lock_chance: float = 0.75
    key_chance: float = 0.5
    max_rooms_per_area: int = 6
    min_rooms_per_area: int = 3
    start_area_size = 5
    altar_count = 3
    parameter_chances: RoomParameterCollection = field(default_factory=lambda: RoomParameterCollection())
    target_difficulty: RoomParameterCollection = field(default_factory=lambda: RoomParameterCollection())
