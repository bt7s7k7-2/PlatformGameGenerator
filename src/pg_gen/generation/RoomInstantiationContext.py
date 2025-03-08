from copy import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from ..actors.Placeholders import Placeholder
from ..actors.support.PersistentObject import PersistentObject
from ..difficulty.DifficultyProvider import DifficultyProvider
from ..difficulty.DifficultyReport import DifficultyReport
from ..support.constants import ROOM_WIDTH
from ..support.Point import Point
from ..world.Actor import Actor
from ..world.World import World
from .RoomInfo import RoomConnectionCollection
from .RoomParameter import RoomParameterCollection

if TYPE_CHECKING:
    from .RoomInfo import RoomInfo


@dataclass
class RoomInstantiationContext(RoomParameterCollection, RoomConnectionCollection):
    flip: bool
    room: "RoomInfo"
    world: World
    difficulty: DifficultyReport | None
    offset: Point = Point.ZERO
    only_once_rooms: set[str] = field(default_factory=lambda: set())

    _parent: "RoomInstantiationContext | None" = field(default=None, kw_only=True)
    _next_flag = 0

    def get_next_flag_id(self):
        if self._parent is not None:
            return self._parent.get_next_flag_id()
        self._next_flag += 1
        return self._next_flag - 1

    def get_next_flag(self):
        assert self.room is not None

        flag = self.get_next_flag_id()

        while len(self.room.persistent_flags) <= flag:
            self.room.persistent_flags.append(None)

        return flag

    def handle_actor(self, actor: Actor, _):
        if self.offset != Point.ZERO:
            actor.position += self.offset

        if self.flip:
            center = actor.position + actor.size * 0.5
            room_width = ROOM_WIDTH
            room_center = room_width * 0.5
            center = Point(room_center - (center.x - room_center), center.y)
            actor.position = center - actor.size * 0.5
            actor.flip_x()

        return self.handle_placeholder(actor)

    def handle_placeholder(self, actor: Actor) -> Literal[False] | None:
        if isinstance(actor, PersistentObject):
            actor.init_persistent_object(self.room, self.get_next_flag())
        
        if self.difficulty is not None and isinstance(actor, DifficultyProvider):
            actor.apply_difficulty(self.difficulty)

        if isinstance(actor, Placeholder):
            replacement = actor.evaluate_placeholder(self)

            if replacement == actor:
                return None

            if isinstance(replacement, bool):
                return replacement

            replacement.universe = self.world.universe

            result = self.handle_placeholder(replacement)
            if result == False:
                return False

            self.world.add_actor(replacement)

            return False

    def create_child(self, offset: Point | None = None):
        child = copy(self)
        child._parent = self
        if offset is not None:
            child.offset = offset
        return child
