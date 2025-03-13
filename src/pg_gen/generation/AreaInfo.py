from dataclasses import dataclass, field

from .RoomInfo import RoomInfo


@dataclass
class AreaInfo:
    id: int
    parent: int | None
    depth: int
    rooms: list[RoomInfo] = field(default_factory=lambda: [])
