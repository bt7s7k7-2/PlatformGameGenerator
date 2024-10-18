from dataclasses import dataclass, field


from ...level_editor.ActorRegistry import ActorRegistry
from .Climbable import Climbable


@dataclass
class Ladder(Climbable):
    sprite: str = field(default="ladder_sprite")


ActorRegistry.register_actor(Ladder)
