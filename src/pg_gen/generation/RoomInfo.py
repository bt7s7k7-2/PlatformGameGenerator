from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, List, Literal

from ..support.Direction import Direction
from ..support.ObjectManifest import ObjectManifest
from ..support.Point import Point
from .RoomParameter import RoomParameterCollection

if TYPE_CHECKING:
    from .RoomPrefab import RoomPrefab

NOT_CONNECTED = -1
NO_KEY = 0


@dataclass
class RoomConnectionCollection:
    _connections: List[int] = field(default_factory=lambda: [NOT_CONNECTED] * 4, init=False)

    def get_connection(self, direction: Direction):
        return self._connections[direction]

    def set_connection(self, direction: Direction, value: int):
        self._connections[direction] = value

    def copy_connections(self, source: "RoomConnectionCollection"):
        for i, value in enumerate(source._connections):
            self._connections[i] = value

    @staticmethod
    def get_manifest() -> ObjectManifest:
        connection_type = Literal[-1, 1, 0]
        return [
            (("up", [RoomInfo.get_connection, Direction.UP], [RoomInfo.set_connection, Direction.UP]), connection_type),
            (("left", [RoomInfo.get_connection, Direction.LEFT], [RoomInfo.set_connection, Direction.LEFT]), connection_type),
            (("down", [RoomInfo.get_connection, Direction.DOWN], [RoomInfo.set_connection, Direction.DOWN]), connection_type),
            (("right", [RoomInfo.get_connection, Direction.RIGHT], [RoomInfo.set_connection, Direction.RIGHT]), connection_type),
        ]


@dataclass
class RoomInfo(RoomParameterCollection, RoomConnectionCollection):
    seed: float
    position: Point
    area: int
    prefab: "RoomPrefab | None" = None
    provides_key: int = NO_KEY
    persistent_flags: List[Any] = field(default_factory=lambda: [], init=False)

    @staticmethod
    def get_manifest() -> ObjectManifest:
        key_type = Literal[0, 1]

        return [
            *RoomConnectionCollection.get_manifest(),
            ("provides_key", key_type),
            *RoomParameterCollection.get_manifest(),
        ]
