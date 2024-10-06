from copy import copy
from dataclasses import dataclass
from typing import Dict, Type

from ..world.Actor import Actor


@dataclass
class ActorType:
    name: str
    type: Type[Actor]
    default_value: Actor | None

    def create_instance(self):
        if self.default_value is not None:
            return copy(self.default_value)
        else:
            return self.type()


class ActorRegistry:

    _types: Dict[str, ActorType] = {}

    @staticmethod
    def find_actor_type(name: str):
        return ActorRegistry._types[name]

    @staticmethod
    def get_actor_types():
        return ActorRegistry._types.items()

    @staticmethod
    def register_actor[T: Actor](type: Type[T], /, suffix: str | None = None, default_value: T | None = None):
        name = type.__name__
        if suffix != None:
            name += ":" + suffix

        ActorRegistry._types[name] = ActorType(name, type, default_value)
