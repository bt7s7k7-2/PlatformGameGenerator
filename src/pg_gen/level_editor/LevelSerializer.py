import json
from copy import copy
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Literal

from ..actors.support.ConfigurableObject import ConfigurableObject
from ..support.Point import Point
from ..world.Actor import Actor
from .ActorRegistry import ActorRegistry, ActorType

if TYPE_CHECKING:
    from ..world.World import World

_JSON_CACHE: dict[str, Any] = {}


class LevelSerializer:
    @staticmethod
    def serialize(actors: List[Actor], types: List[ActorType], aux_data: Dict):
        actors_data = [
            {
                "pos": actor.position.serialize(),
                "size": actor.size.serialize(),
                "type": types[i].name + "," + actor.config if isinstance(actor, ConfigurableObject) else types[i].name,
            }
            for i, actor in enumerate(actors)
        ]

        data = {"actors": actors_data, **aux_data}

        return json.dumps(data, indent=4, sort_keys=True) + "\n"

    @staticmethod
    def deserialize(world: "World", raw_data: str, spawn_callback: Callable[[Actor, ActorType], Literal[False] | None] | None = None):
        data = _JSON_CACHE.get(raw_data)
        if data is None:
            data = json.loads(raw_data)
            _JSON_CACHE[raw_data] = data
        data = copy(data)

        actors = data["actors"]
        del data["actors"]

        for actor_data in actors:
            position = Point.deserialize(actor_data["pos"])
            size = Point.deserialize(actor_data["size"])

            type_name: str = actor_data["type"]
            config = None
            if "," in type_name:
                type_name, _, config = type_name.partition(",")

            type = ActorRegistry.find_actor_type(type_name)
            actor = type.create_instance()

            if config is not None and isinstance(actor, ConfigurableObject):
                actor.apply_config(config)

            actor.position = position
            actor.size = size

            if spawn_callback is not None:
                if spawn_callback(actor, type) == False:
                    continue

            world.add_actor(actor)

        return data
