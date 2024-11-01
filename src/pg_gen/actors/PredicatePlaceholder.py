from copy import copy
from dataclasses import dataclass
from enum import Enum
from random import Random
from typing import Any

from ..game_core.Camera import CameraClient
from ..game_core.ResourceClient import ResourceClient
from ..level_editor.ActorRegistry import ActorRegistry
from ..support.Color import Color
from ..support.constants import TEXT_BG_COLOR, TEXT_COLOR
from ..world.Actor import Actor
from .Gem import Gem
from .support.PersistentObject import PersistentObject
from .support.SpriteActor import SpriteActor


class PredicateType(Enum):
    NONE = 0
    CHANCE = 1


class PredicatePlaceholderState(Enum):
    DEFAULT = 0
    INACTIVE = 1
    ACTIVE = 2


@dataclass(kw_only=True)
class PredicatePlaceholder(PersistentObject[PredicatePlaceholderState], ResourceClient, CameraClient, Actor):
    actor: Actor
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
            actor = copy(self.actor)
            actor.position = self.position
            actor.size = self.size
            return actor

        return None

    def draw(self):
        self.actor.position = self.position
        self.actor.universe = self.universe
        self.actor.world = self.world
        self.actor.size = self.size
        if isinstance(self.actor, SpriteActor):
            self.actor.tint = Color.YELLOW
        self.actor.draw()

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
        actor=Gem(),
        predicate_type=PredicateType.CHANCE,
        predicate_value=0.5,
    ),
)

ActorRegistry.register_actor(
    PredicatePlaceholder,
    name_override="Gem:25%",
    default_value=PredicatePlaceholder(
        actor=Gem(),
        predicate_type=PredicateType.CHANCE,
        predicate_value=0.25,
    ),
)
