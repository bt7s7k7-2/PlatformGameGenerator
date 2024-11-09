from dataclasses import dataclass, field


@dataclass
class RoomPrefabParameters:
    groups: list[str] = field(default_factory=lambda: [])
