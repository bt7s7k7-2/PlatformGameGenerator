import json
from typing import TYPE_CHECKING, Callable, Dict, List

from ..support.Point import Point
from ..world.Actor import Actor
from .ActorRegistry import ActorRegistry, ActorType

if TYPE_CHECKING:
    from ..world.World import World


class LevelSerializer:
    @staticmethod
    def serialize(actors: List[Actor], types: List[ActorType], aux_data: Dict):
        actors_data = [
            {
                "pos": actor.position.serialize(),
                "size": actor.size.serialize(),
                "type": types[i].name,
            }
            for i, actor in enumerate(actors)
        ]

        data = {"actors": actors_data, **aux_data}

        return json.dumps(data, indent=4, sort_keys=True)

    @staticmethod
    def deserialize(world: "World", raw_data: str, spawn_callback: Callable[[Actor, ActorType], None] | None = None):
        data = json.loads(raw_data)
        actors = data["actors"]
        del data["actors"]

        for actor_data in actors:
            position = Point.deserialize(actor_data["pos"])
            size = Point.deserialize(actor_data["size"])
            type = ActorRegistry.find_actor_type(actor_data["type"])

            actor = type.create_instance()
            actor.position = position
            actor.size = size

            world.add_actor(actor)

            if spawn_callback is not None:
                spawn_callback(actor, type)

        return data
