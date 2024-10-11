from copy import copy
from dataclasses import dataclass
from importlib import import_module
from os import path, walk
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
    def register_actor[T: Actor](type: Type[T], /, suffix: str | None = None, name_override: str | None = None, default_value: T | None = None):
        name = type.__name__
        if suffix != None:
            name += ":" + suffix

        if name_override is not None:
            name = name_override

        ActorRegistry._types[name] = ActorType(name, type, default_value)

    @staticmethod
    def load_actors():
        curr_dir = path.dirname(__file__)
        entities_folder = path.normpath(path.join(curr_dir, "../entities"))
        for directory, _, files in walk(entities_folder, onerror=print):
            for file in files:
                file = path.join(directory, file)
                if not file.endswith(".py"):
                    continue
                relative_path = path.relpath(file, curr_dir)
                module_import = relative_path.replace("../", "..").replace("/", ".")[:-3]
                import_module(module_import, __package__)
