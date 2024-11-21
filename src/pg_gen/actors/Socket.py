from copy import copy
from random import Random
from typing import Any, Literal, override

from pg_gen.generation.RoomInstantiationContext import RoomInstantiationContext
from pg_gen.world.Actor import Actor

from ..game_core.Camera import CameraClient
from ..game_core.ResourceClient import ResourceClient
from ..generation.RoomPrefab import RoomPrefab
from ..generation.RoomPrefabRegistry import RoomPrefabRegistry
from ..level_editor.ActorRegistry import ActorRegistry
from ..support.Color import Color
from ..support.constants import TEXT_BG_COLOR, TEXT_COLOR
from ..support.Point import Point
from .Placeholders import Placeholder
from .support.ConfigurableObject import ConfigurableObject
from .support.PersistentObject import PersistentObject


class Socket(PersistentObject[RoomPrefab | None], CameraClient, ConfigurableObject, ResourceClient, Placeholder):
    @property
    def size_string(self):
        return f"{self.size.x}x{self.size.y}"

    @override
    def _get_default_persistent_value(self) -> Any:
        return None

    @override
    def draw(self):
        infill_color = Color.BLACK
        self._camera.draw_placeholder(self.position, self.size, Color.CYAN * 0.75, width=2)
        for y in [0, self.size.y - 1 / self._camera.zoom]:
            self._camera.draw_placeholder_raw(self._camera.world_to_screen(self.position + Point(0.5, y)), Point(self.size.x - 1, 0) * self._camera.zoom + Point(0, 1), infill_color)
        for x in [0, self.size.x - 1 / self._camera.zoom]:
            self._camera.draw_placeholder_raw(self._camera.world_to_screen(self.position + Point(x, 0.5)), Point(0, self.size.y - 1) * self._camera.zoom + Point(1, 0), infill_color)

        self._resource_provider.font.render_to(
            self._camera.screen,
            (self._camera.world_to_screen(self.position) + Point(0, 12)).to_pygame_coordinates(),
            self.size_string,
            fgcolor=TEXT_COLOR,
            bgcolor=TEXT_BG_COLOR,
        )

    @override
    def evaluate_placeholder(self, context: RoomInstantiationContext) -> Actor | Literal[False]:
        room = self.persistent_value

        if room is None:
            rooms = RoomPrefabRegistry.find_rooms(self.config, requirements=None, context=context)
            room = Random(context.room.seed + self.flag_index).choice(rooms)
            self.persistent_value = room

        offset_context = copy(context)
        offset_context.offset = self.position

        room.instantiate_using(offset_context)
        return False


ActorRegistry.register_actor(Socket)
