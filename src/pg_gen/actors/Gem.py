from dataclasses import dataclass, field
from typing import Any, Literal, override

from pg_gen.difficulty.DifficultyReport import DifficultyReport
from pg_gen.generation.RoomInstantiationContext import RoomInstantiationContext
from pg_gen.world.Actor import Actor

from ..difficulty.DifficultyProvider import DifficultyProvider
from ..generation.RoomParameter import RoomParameter
from ..level_editor.ActorRegistry import ActorRegistry
from ..world.CollisionFlags import CollisionFlags
from .Placeholders import Placeholder
from .Player import Player
from .support.PersistentObject import PersistentObject
from .support.SpriteActor import SpriteActor


@dataclass
class Gem(SpriteActor, PersistentObject[bool], Placeholder, DifficultyProvider):
    sprite: str | None = field(default="gem_sprite")
    collision_flags: CollisionFlags = CollisionFlags.TRIGGER

    def _get_default_persistent_value(self) -> Any:
        return True

    def evaluate_placeholder(self, context: RoomInstantiationContext) -> Actor | Literal[False]:
        if self.persistent_value == False:
            return False

        return self

    def on_trigger(self, trigger: Actor):
        if isinstance(trigger, Player):
            trigger.score += 10
            self.universe.queue_task(lambda: self.remove())
            self.persistent_value = False
        return super().on_trigger(trigger)

    @override
    def apply_difficulty(self, difficulty: DifficultyReport):
        difficulty.increment_parameter(RoomParameter.REWARD, 1)


ActorRegistry.register_actor(Gem)
