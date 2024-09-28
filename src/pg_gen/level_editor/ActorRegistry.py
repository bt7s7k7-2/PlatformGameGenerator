from dataclasses import dataclass
from typing import Any, Dict, Type

from ..entities.Door import Door
from ..entities.Key import Key
from ..entities.Wall import Wall
from ..world.Actor import Actor


@dataclass
class ActorType:
    name: str
    type: Type[Actor]
    arguments: Dict[str, Any]


class ActorRegistry:

    _actor: Dict[str, Type[Actor]] = {}

    @staticmethod
    def get_actor_types():
        return ActorRegistry._actor.items()

    @staticmethod
    def register_actor[T: Actor](type: Type[T]):
        ActorRegistry._actor[type.__name__] = type


ActorRegistry.register_actor(Door)
ActorRegistry.register_actor(Wall)
ActorRegistry.register_actor(Key)
