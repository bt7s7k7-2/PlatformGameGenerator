from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from ..actors.Placeholders import Placeholder
from ..actors.support.PersistentObject import PersistentObject
from ..support.constants import ROOM_WIDTH
from ..support.Point import Point
from ..world.Actor import Actor
from ..world.World import World

if TYPE_CHECKING:
    from .RoomInfo import RoomInfo


@dataclass
class RoomInstantiationContext:
    flip: bool
    room: "RoomInfo"
    world: World
    offset: Point = Point.ZERO
    next_flag = 0

    def get_next_flag(self):
        assert self.room is not None

        flag = self.next_flag
        self.next_flag += 1

        if len(self.room.persistent_flags) <= flag:
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

        if isinstance(actor, Placeholder):
            replacement = actor.evaluate_placeholder(self)
            if isinstance(replacement, bool):
                return replacement
            replacement.universe = self.world.universe
            self.world.add_actor(replacement)
            self.handle_placeholder(replacement)
            return False
