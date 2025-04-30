from copy import copy
from dataclasses import dataclass
from importlib import import_module
from importlib.abc import Traversable
from typing import Type

from ..assets import get_pg_assets, walk_files_recursive
from ..support.Point import Point
from ..world.Actor import Actor


@dataclass
class ActorType:
    name: str
    type: Type[Actor]
    default_value: Actor | None
    offset: Point = Point.ZERO

    def create_instance(self):
        if self.default_value is not None:
            return copy(self.default_value)
        else:
            return self.type()


class ActorRegistry:

    _types: dict[str, ActorType] = {}
    _types_array: list[tuple[str, ActorType]] = []

    @staticmethod
    def find_actor_type(name: str):
        return ActorRegistry._types[name]

    @staticmethod
    def try_find_actor_type(name: str):
        return ActorRegistry._types.get(name, None)

    @staticmethod
    def get_actor_types():
        return ActorRegistry._types_array

    @staticmethod
    def register_actor[T: Actor](type: Type[T], /, suffix: str | None = None, name_override: str | None = None, default_value: T | None = None):
        name = type.__name__
        if suffix != None:
            name += ":" + suffix

        if name_override is not None:
            name = name_override

        ActorRegistry._types[name] = ActorType(name, type, default_value)

    @staticmethod
    def load_actors():
        assets = get_pg_assets()

        def load_actor(file: Traversable, path: str):
            if not path.endswith(".py"):
                return
            module_name = "pg_gen.actors" + path[:-3]
            import_module(module_name, __package__)

        walk_files_recursive(assets.actors, load_actor)

        ActorRegistry._types_array = sorted([(name, value) for name, value in ActorRegistry._types.items()], key=lambda x: x[0])
