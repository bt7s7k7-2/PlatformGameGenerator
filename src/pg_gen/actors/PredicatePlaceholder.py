from dataclasses import dataclass, field
from enum import Enum
from random import Random
from typing import Any, override

from ..game_core.Camera import CameraClient
from ..game_core.ResourceClient import ResourceClient
from ..level_editor.ActorRegistry import ActorRegistry, ActorType
from ..support.Color import Color
from ..world.Actor import Actor
from .support.ConfigurableObject import ConfigurableObject
from .support.PersistentObject import PersistentObject


class PredicateType(Enum):
    NONE = 0
    CHANCE = 1


class PredicatePlaceholderState(Enum):
    DEFAULT = 0
    INACTIVE = 1
    ACTIVE = 2


@dataclass
class PredicatePlaceholderConfig:
    actor: ActorType
    type: PredicateType = PredicateType.NONE
    chance: float = 1.0


@dataclass(kw_only=True)
class PredicatePlaceholder(PersistentObject[PredicatePlaceholderState], ResourceClient, CameraClient, ConfigurableObject):
    _actor_instance: Actor | None = field(default=None, init=False)

    def _get_default_persistent_value(self) -> Any:
        return PredicatePlaceholderState.DEFAULT

    @override
    def apply_config(self, config: str) -> bool:
        super().apply_config(config)

        if self.parse_config() is None:
            return False

        return True

    def parse_config(self):
        arguments = self.config.split(",")
        if len(arguments) < 1:
            return None

        actor = ActorRegistry.try_find_actor_type(arguments.pop(0))
        if actor is None:
            return None

        config = PredicatePlaceholderConfig(actor)
        while len(arguments) > 0:
            argument = arguments.pop(0)
            if len(argument) == 0:
                continue

            if argument[-1] == "%":
                try:
                    config.chance = int(argument[0:-1]) / 100
                except ValueError:
                    return None

                config.type = PredicateType.CHANCE
                continue

            return None
        return config

    def evaluate_predicate(self):
        state = self.persistent_value
        assert self.room is not None

        config = self.parse_config()
        if config is None:
            return None

        if state == PredicatePlaceholderState.DEFAULT:
            if config.type == PredicateType.NONE:
                state = PredicatePlaceholderState.ACTIVE
            elif config.type == PredicateType.CHANCE:
                if self.room is None:
                    state = PredicatePlaceholderState.ACTIVE if Random().random() < config.chance else PredicatePlaceholderState.INACTIVE
                else:
                    state = PredicatePlaceholderState.ACTIVE if Random(self.room.seed + self.flag_index).random() < config.chance else PredicatePlaceholderState.INACTIVE

        self.persistent_value = state

        if state == PredicatePlaceholderState.ACTIVE:
            actor = config.actor.create_instance()
            actor.position = self.position
            actor.size = self.size
            return actor

        return None

    def draw(self):
        config = self.parse_config()
        if config is None:
            if self._actor_instance is not None:
                instance = self._actor_instance
                self._actor_instance = None
                self.universe.queue_task(lambda: instance.remove())

            return super().draw()

        self._actor_instance = self._actor_instance or config.actor.create_instance()
        self._actor_instance.position = self.position
        self._actor_instance.universe = self.universe
        self._actor_instance.world = self.world
        self._actor_instance.size = self.size
        if hasattr(self._actor_instance, "tint"):
            self._actor_instance.tint = Color.YELLOW  # type: ignore
        self._actor_instance.draw()

        return super().draw()


ActorRegistry.register_actor(PredicatePlaceholder, name_override="Placeholder")
