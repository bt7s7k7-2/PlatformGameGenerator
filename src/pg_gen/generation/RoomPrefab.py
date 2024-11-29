from copy import copy
from dataclasses import dataclass, field
from enum import Enum

from ..level_editor.LevelSerializer import LevelSerializer
from ..support.Direction import Direction
from ..support.ObjectManifest import ObjectManifest
from ..support.Point import Point
from ..world.World import World
from .RoomController import RoomController
from .RoomInfo import NOT_CONNECTED, RoomInfo
from .RoomInstantiationContext import RoomInstantiationContext
from .RoomTrigger import RoomTrigger


class RoomPrefabEntrance(Enum):
    CLOSED = 0
    DOOR = 1
    WALL = 2
    ANY = 3
    OPEN = 4

    @classmethod
    def from_string(cls, input: str | None):
        if input == None or input == "closed":
            return cls.CLOSED
        if input == "door":
            return cls.DOOR
        if input == "wall":
            return cls.WALL
        if input == "any":
            return cls.ANY
        if input == "open":
            return cls.OPEN
        raise RuntimeError("Invalid entrance type")


@dataclass
class RoomPrefab:
    name: str
    data: str = field(repr=False)

    groups: list[str] = field(default_factory=lambda: [])

    _connections: list[RoomPrefabEntrance] = field(default_factory=lambda: [RoomPrefabEntrance(0)] * 4, init=False)
    _is_flipped: bool = False

    def get_connection(self, direction: Direction):
        return self._connections[direction]

    def set_connection(self, direction: Direction, value: RoomPrefabEntrance):
        self._connections[direction] = value

    @staticmethod
    def get_manifest() -> ObjectManifest:
        return [
            (("up", [RoomPrefab.get_connection, Direction.UP], [RoomPrefab.set_connection, Direction.UP]), RoomPrefabEntrance),
            (("left", [RoomPrefab.get_connection, Direction.LEFT], [RoomPrefab.set_connection, Direction.LEFT]), RoomPrefabEntrance),
            (("down", [RoomPrefab.get_connection, Direction.DOWN], [RoomPrefab.set_connection, Direction.DOWN]), RoomPrefabEntrance),
            (("right", [RoomPrefab.get_connection, Direction.RIGHT], [RoomPrefab.set_connection, Direction.RIGHT]), RoomPrefabEntrance),
            ("key", bool),
            ("allow_flip", bool),
            ("only_once", bool),
            ("groups", list[str]),
        ]

    key: bool = False

    allow_flip = False
    only_once = False

    def flip(self):
        assert not self._is_flipped
        flipped = copy(self)
        flipped._connections = copy(self._connections)
        flipped._is_flipped = True
        flipped.name = self.name + "`1"

        flipped.set_connection(Direction.LEFT, self.get_connection(Direction.RIGHT))
        flipped.set_connection(Direction.RIGHT, self.get_connection(Direction.LEFT))

        return flipped

    def instantiate_root(self, room: RoomInfo, controller: RoomController | None, world: World):
        context = RoomInstantiationContext(flip=self._is_flipped, room=room, world=world)
        context.copy_connections(room)
        self.instantiate_using(context)

        if controller is None:
            return

        for direction, position, size in [
            (Direction.LEFT, Point(-1.5, 2), Point(1, 2)),
            (Direction.RIGHT, Point(18.5, 2), Point(1, 2)),
            (Direction.DOWN, Point(8, 11.5), Point(3, 1)),
            (Direction.UP, Point(8, -1.5), Point(3, 1)),
        ]:
            if room.get_connection(direction) != NOT_CONNECTED:
                world.add_actor(
                    RoomTrigger(
                        position=position,
                        size=size,
                        room_controller=controller,
                        direction=direction,
                    )
                )

    def _get_properties_in_context(self, context: RoomInstantiationContext):
        # We XOR our flip value with the context flip value so we flip correctly in
        # flipped context, for example if we are in a flipped context and our flip
        # value is false we will be flipped.
        is_flipped = context.flip != self._is_flipped
        name = self.name

        if is_flipped:
            if self._is_flipped:
                pass
            else:
                name += "`1"
        else:
            if self._is_flipped:
                name = name[0:-2]
            else:
                pass

        return is_flipped, name

    def is_usable_in_context(self, context: RoomInstantiationContext):
        _, name = self._get_properties_in_context(context)
        return not self.only_once or name not in context.only_once_rooms

    def instantiate_using(self, context: RoomInstantiationContext):
        prev_value = context.flip
        is_flipped, name = self._get_properties_in_context(context)
        context.flip = is_flipped

        if self.only_once:
            assert name not in context.only_once_rooms
            context.only_once_rooms.add(name)

        LevelSerializer.deserialize(context.world, self.data, context.handle_actor)
        context.flip = prev_value
