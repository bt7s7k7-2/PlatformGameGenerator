from dataclasses import dataclass
from typing import override

from ..generation.RoomParameter import RoomParameter, RoomParameterCollection


@dataclass
class DifficultyReport(RoomParameterCollection):
    @override
    def __str__(self) -> str:
        return ", ".join(f"{parameter.name.lower()}: {value:.2f}" for (parameter, value) in zip(RoomParameter, self._parameters))
