from dataclasses import dataclass, field
from enum import Enum
from random import Random
from typing import Any

from ..game_core.Camera import CameraClient
from ..game_core.ResourceClient import ResourceClient
from ..level_editor.ActorRegistry import ActorRegistry
from ..support.Color import Color
from ..support.constants import TEXT_BG_COLOR, TEXT_COLOR
from ..world.Actor import Actor
from .support.PersistentObject import PersistentObject


class PredicateType(Enum):
    NONE = 0
    CHANCE = 1


class PredicatePlaceholderState(Enum):
    DEFAULT = 0
    INACTIVE = 1
    ACTIVE = 2


@dataclass(kw_only=True)
class PredicatePlaceholder(PersistentObject[PredicatePlaceholderState], ResourceClient, CameraClient, Actor):
    actor: str
    _actor_instance: Actor | None = field(default=None, init=False)
    predicate_type: PredicateType
    predicate_value: float

    def _get_default_persistent_value(self) -> Any:
        return PredicatePlaceholderState.DEFAULT

    def evaluate_predicate(self):
        state = self.persistent_value
        assert self.room is not None

        if state == PredicatePlaceholderState.DEFAULT:
            if self.predicate_type == PredicateType.NONE:
                state = PredicatePlaceholderState.ACTIVE
            elif self.predicate_type == PredicateType.CHANCE:
                if self.room is None:
                    state = PredicatePlaceholderState.ACTIVE if Random().random() < self.predicate_value else PredicatePlaceholderState.INACTIVE
                else:
                    state = PredicatePlaceholderState.ACTIVE if Random(self.room.seed + self.flag_index).random() < self.predicate_value else PredicatePlaceholderState.INACTIVE

        self.persistent_value = state

        if state == PredicatePlaceholderState.ACTIVE:
            actor = ActorRegistry.find_actor_type(self.actor).create_instance()
            actor.position = self.position
            actor.size = self.size
            return actor

        return None

    def draw(self):
        self._actor_instance = self._actor_instance or ActorRegistry.find_actor_type(self.actor).create_instance()
        self._actor_instance.position = self.position
        self._actor_instance.universe = self.universe
        self._actor_instance.world = self.world
        self._actor_instance.size = self.size
        if hasattr(self._actor_instance, "tint"):
            self._actor_instance.tint = Color.YELLOW  # type: ignore
        self._actor_instance.draw()

        self._resource_provider.font.render_to(
            self._camera.screen,
            self._camera.world_to_screen(self.position).to_pygame_coordinates(),
            f"{self.predicate_type.name[:2]} {self.predicate_value}",
            TEXT_COLOR,
            TEXT_BG_COLOR,
        )

        return super().draw()


ActorRegistry.register_actor(
    PredicatePlaceholder,
    name_override="Gem:50%",
    default_value=PredicatePlaceholder(
        actor="Gem",
        predicate_type=PredicateType.CHANCE,
        predicate_value=0.5,
    ),
)

ActorRegistry.register_actor(
    PredicatePlaceholder,
    name_override="Gem:25%",
    default_value=PredicatePlaceholder(
        actor="Gem",
        predicate_type=PredicateType.CHANCE,
        predicate_value=0.25,
    ),
)

ActorRegistry.register_actor(
    PredicatePlaceholder,
    name_override="Skull:50%",
    default_value=PredicatePlaceholder(
        actor="Skull:roll",
        predicate_type=PredicateType.CHANCE,
        predicate_value=0.5,
    ),
)

ActorRegistry.register_actor(
    PredicatePlaceholder,
    name_override="Blocker:50%",
    default_value=PredicatePlaceholder(
        actor="Blocker",
        predicate_type=PredicateType.CHANCE,
        predicate_value=0.5,
    ),
)

ActorRegistry.register_actor(
    PredicatePlaceholder,
    name_override="Bobber:50%",
    default_value=PredicatePlaceholder(
        actor="Bobber",
        predicate_type=PredicateType.CHANCE,
        predicate_value=0.5,
    ),
)

ActorRegistry.register_actor(
    PredicatePlaceholder,
    name_override="Wall:75%",
    default_value=PredicatePlaceholder(
        actor="Wall",
        predicate_type=PredicateType.CHANCE,
        predicate_value=0.75,
    ),
)

ActorRegistry.register_actor(
    PredicatePlaceholder,
    name_override="Wall:50%",
    default_value=PredicatePlaceholder(
        actor="Wall",
        predicate_type=PredicateType.CHANCE,
        predicate_value=0.5,
    ),
)

ActorRegistry.register_actor(
    PredicatePlaceholder,
    name_override="Wall:25%",
    default_value=PredicatePlaceholder(
        actor="Wall",
        predicate_type=PredicateType.CHANCE,
        predicate_value=0.25,
    ),
)
