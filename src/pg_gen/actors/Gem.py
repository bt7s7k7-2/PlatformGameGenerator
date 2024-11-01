from dataclasses import dataclass, field

from pg_gen.world.Actor import Actor

from ..level_editor.ActorRegistry import ActorRegistry
from ..world.CollisionFlags import CollisionFlags
from .Player import Player
from .support.SpriteActor import SpriteActor


@dataclass
class Gem(SpriteActor):
    sprite: str | None = field(default="gem_sprite")
    collision_flags: CollisionFlags = CollisionFlags.TRIGGER

    def on_trigger(self, trigger: Actor):
        if isinstance(trigger, Player):
            trigger.score += 10
            self.universe.queue_task(lambda: self.remove())
        return super().on_trigger(trigger)


ActorRegistry.register_actor(Gem)
