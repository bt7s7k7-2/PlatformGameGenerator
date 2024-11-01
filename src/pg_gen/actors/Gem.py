from dataclasses import dataclass, field
from typing import Any

from pg_gen.world.Actor import Actor

from ..level_editor.ActorRegistry import ActorRegistry
from ..world.CollisionFlags import CollisionFlags
from .Player import Player
from .support.PersistentObject import PersistentObject
from .support.SpriteActor import SpriteActor


@dataclass
class Gem(SpriteActor, PersistentObject[bool]):
    sprite: str | None = field(default="gem_sprite")
    collision_flags: CollisionFlags = CollisionFlags.TRIGGER

    def _get_default_persistent_value(self) -> Any:
        return True

    def on_created(self):
        if self.persistent_value == False:
            self.universe.queue_task(lambda: self.remove())

    def on_trigger(self, trigger: Actor):
        if isinstance(trigger, Player):
            trigger.score += 10
            self.universe.queue_task(lambda: self.remove())
            self.persistent_value = False
        return super().on_trigger(trigger)


ActorRegistry.register_actor(Gem)
