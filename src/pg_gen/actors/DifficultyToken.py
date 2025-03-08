from typing import override

from ..difficulty.DifficultyProvider import DifficultyProvider
from ..difficulty.DifficultyReport import DifficultyReport
from ..game_core.Camera import CameraClient
from ..generation.RoomParameter import RoomParameter
from ..level_editor.ActorRegistry import ActorRegistry
from ..support.Color import Color
from .support.ConfigurableObject import ConfigurableObject


class DifficultyToken(ConfigurableObject, DifficultyProvider, CameraClient):
    @override
    def apply_config(self, config: str) -> bool:
        super().apply_config(config)

        parsed = self.parse_config(config)
        if parsed is None:
            return False

        return True

    def parse_config(self, config: str):
        segments = config.split(",")
        if len(segments) != 2:
            return None

        parameter_name, value_string = segments
        parameter_name = parameter_name.upper()
        if parameter_name not in RoomParameter._member_map_:
            return None
        parameter = RoomParameter[parameter_name]
        try:
            value = float(value_string)
        except ValueError:
            return None

        return (parameter, value)

    @override
    def apply_difficulty(self, difficulty: DifficultyReport):
        config = self.parse_config(self.config)
        if config is None:
            return

        parameter, value = config
        difficulty.increment_parameter(parameter, value)

    @override
    def draw(self):
        super().draw()
        self._camera.draw_placeholder(self.position, self.size, Color.RED, width=1)


ActorRegistry.register_actor(DifficultyToken, name_override="Token")
