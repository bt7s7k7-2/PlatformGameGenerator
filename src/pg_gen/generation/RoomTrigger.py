from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..entities.Player import Player
from ..game_core.Camera import CameraClient
from ..support.Color import Color
from ..support.Direction import Direction
from ..world.Actor import Actor
from ..world.CollisionFlags import CollisionFlags

if TYPE_CHECKING:
    from .RoomController import RoomController


@dataclass
class RoomTrigger(CameraClient):
    collision_flags: CollisionFlags = field(default=CollisionFlags.TRIGGER)
    room_controller: "RoomController" = field(default=None, repr=False)  # type: ignore
    direction: Direction = field(default=Direction.UP)

    def on_trigger(self, trigger: Actor):
        if not isinstance(trigger, Player):
            return

        self.room_controller.switch_rooms(self.direction)

    def draw(self):
        self._camera.draw_placeholder(self.position, self.size, Color.GREEN)
