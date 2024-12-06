from dataclasses import dataclass, field
from enum import Enum

from ..support.ObjectManifest import ObjectManifest


class RoomParameter(Enum):
    ENEMY = 0
    JUMP = 1
    REWARD = 2
    SPRAWL = 3


@dataclass
class RoomParameterCollection:
    _parameters: list[float] = field(default_factory=lambda: [0] * len(RoomParameter._member_map_), kw_only=True)

    def get_parameter(self, parameter: RoomParameter):
        return self._parameters[parameter.value]

    def set_parameter(self, parameter: RoomParameter, value: float):
        self._parameters[parameter.value] = value
        return self

    def set_all_parameters(self, value: float):
        self._parameters = [value] * len(RoomParameter._member_map_)
        return self

    def copy_parameters(self, source: "RoomParameterCollection"):
        for i, value in enumerate(source._parameters):
            self._parameters[i] = value

    @staticmethod
    def get_manifest() -> ObjectManifest:
        return [((name.lower(), [RoomParameterCollection.get_parameter, value], [RoomParameterCollection.set_parameter, value]), float) for name, value in RoomParameter._member_map_.items()]
