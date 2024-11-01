from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ...world.Actor import Actor

if TYPE_CHECKING:
    from ...generation.RoomInfo import RoomInfo


@dataclass
class PersistentObject[T](Actor):
    flag_index: int = 0
    room: "RoomInfo | None" = None

    def _get_default_persistent_value(self) -> Any:
        return None

    @property
    def persistent_value(self) -> T:
        if self.room is not None and self.room.persistent_flags[self.flag_index] is not None:
            return self.room.persistent_flags[self.flag_index]
        else:
            return self._get_default_persistent_value()

    @persistent_value.setter
    def persistent_value(self, value: T):
        if self.room is not None:
            self.room.persistent_flags[self.flag_index] = value

    def init_persistent_object(self, room: "RoomInfo", flag_index: int):
        self.room = room
        self.flag_index = flag_index
