from copy import copy
from dataclasses import dataclass, field
from enum import Enum

from ..actors.Placeholders import DoorPlaceholder, KeyPlaceholder, WallPlaceholder
from ..actors.progression.Door import Door
from ..actors.progression.Key import Key
from ..actors.Wall import Wall
from ..level_editor.LevelSerializer import LevelSerializer
from ..support.constants import ROOM_WIDTH
from ..support.Direction import Direction
from ..support.Point import Point
from ..world.Actor import Actor
from ..world.World import World
from .RoomController import RoomController
from .RoomInfo import NO_KEY, NOT_CONNECTED, RoomInfo
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


@dataclass()
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

    key: bool = False

    left_prefab: str | None = None
    right_prefab: str | None = None
    down_prefab: str | None = None
    up_prefab: str | None = None

    def flip(self):
        assert not self._is_flipped
        flipped = copy(self)
        flipped._connections = copy(self._connections)
        flipped._is_flipped = True
        flipped.name = self.name + "`1"

        flipped.set_connection(Direction.LEFT, self.get_connection(Direction.RIGHT))
        flipped.set_connection(Direction.RIGHT, self.get_connection(Direction.LEFT))

        return flipped

    def instantiate(self, room: RoomInfo, controller: RoomController, world: World):
        next_flag = 0
        flip = self._is_flipped

        def get_next_flag():
            assert room is not None
            nonlocal next_flag

            flag = next_flag
            next_flag += 1

            if len(room.persistent_flags) <= flag:
                room.persistent_flags.append(None)

            return flag

        def handle_actor(actor: Actor, _):
            if flip:
                center = actor.position + actor.size * 0.5
                room_width = ROOM_WIDTH
                room_center = room_width * 0.5
                center = Point(room_center - (center.x - room_center), center.y)
                actor.position = center - actor.size * 0.5
                actor.flip_x()

            if isinstance(actor, KeyPlaceholder):
                door_type = room.provides_key
                if door_type != NO_KEY:
                    world.add_actor(Key(position=actor.position, key_type=door_type, room=room))
                actor.remove()
                return

            if isinstance(actor, DoorPlaceholder):
                door_type = room.get_connection(actor.direction.flipX(flip))
                if door_type > NO_KEY:
                    world.add_actor(
                        Door(
                            position=actor.position,
                            key_type=door_type,
                            room=room,
                            flag_index=get_next_flag(),
                        )
                    )
                actor.remove()
                return

            if isinstance(actor, WallPlaceholder):
                door_type = room.get_connection(actor.direction.flipX(flip))
                if door_type == NOT_CONNECTED:
                    world.add_actor(Wall(position=actor.position, size=actor.size))
                actor.remove()
                return

        LevelSerializer.deserialize(world, self.data, handle_actor)

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
