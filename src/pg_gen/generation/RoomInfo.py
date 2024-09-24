from dataclasses import dataclass, field
from typing import Any, List

from ..support.Direction import Direction
from ..support.Point import Point

NOT_CONNECTED = -1
NO_KEY = 0


@dataclass()
class RoomInfo:
    seed: float
    position: Point
    area: int
    provides_key = NO_KEY
    persistent_flags: List[Any] = field(default_factory=lambda: [], init=False)
    _connections: List[int] = field(default_factory=lambda: [NOT_CONNECTED] * 4, init=False)

    def get_connection(self, direction: Direction):
        return self._connections[direction]

    def set_connection(self, direction: Direction, value: int):
        self._connections[direction] = value
