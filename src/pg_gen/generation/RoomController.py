from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..actors.Player import Player
from ..support.constants import JUMP_IMPULSE, ROOM_HEIGHT, ROOM_WIDTH
from ..support.Direction import Direction
from ..support.Point import Point
from ..world.Actor import Actor
from ..world.World import World
from .RoomInfo import RoomInfo

if TYPE_CHECKING:
    from ..game_core.Universe import Universe


@dataclass
class RoomController(Actor):
    room: RoomInfo | None = None

    @property
    def difficulty(self):
        return self.room.difficulty if self.room is not None else None

    def switch_rooms_absolute(self, direction: Direction | None, next_position: Point):
        assert self.room is not None
        assert self.universe.map is not None

        if not self.universe.map.has_room(next_position):
            print(f"Tried to teleport to invalid room {next_position}")
            return

        next_room = self.universe.map.get_room(next_position)
        self.universe.queue_task(
            lambda: (
                RoomController.initialize_and_activate(
                    self.universe,
                    next_room,
                    entrance=direction.invert() if direction is not None else None,
                ),
                None,
            )[1]
        )

    def switch_rooms(self, direction: Direction):
        assert self.room is not None
        offset = Point.from_direction(direction)
        next_position = self.room.position + offset
        self.switch_rooms_absolute(direction, next_position)

    def activate(self):
        self.universe.set_world(self.world)
        return self

    def initialize_room(self, entrance: Direction | None = None):
        assert self.room is not None
        self.room.difficulty.set_all_parameters(0)
        world = World(self.universe)

        if self.room.prefab is not None:
            self.room.prefab.instantiate_root(self.room, self, world)
        else:
            world.paused = True

        player = self.universe.di.try_inject(Player)
        if player is not None:
            player.transfer_world(world)

            if entrance == Direction.LEFT or entrance == Direction.RIGHT:
                player.position = (
                    Point(
                        ROOM_WIDTH / 2 - ((player.position.x + player.size.x / 2) - ROOM_WIDTH / 2) - player.size.x / 2,
                        player.position.y,
                    )
                    - Point.from_direction(entrance) * 0.5
                )
            elif entrance == Direction.UP or entrance == Direction.DOWN:
                player.position = (
                    Point(
                        player.position.x,
                        ROOM_HEIGHT / 2 - ((player.position.y + player.size.y / 2) - ROOM_HEIGHT / 2) - player.size.y / 2,
                    )
                    - Point.from_direction(entrance) * 1
                )

            if entrance == Direction.DOWN:
                player.velocity = Point(player.velocity.x, -JUMP_IMPULSE)

        world.add_actor(self)
        return self

    @staticmethod
    def initialize_and_activate(universe: "Universe", room: RoomInfo, entrance: Direction | None = None):
        return RoomController(universe, room=room).initialize_room(entrance).activate()
