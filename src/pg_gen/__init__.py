import json
import sys
from os import path, walk

import pygame

from .actors.Player import Player
from .debug.MapView import MapView
from .game_core.InteractiveGameLoop import InteractiveGameLoop
from .game_core.Universe import Universe
from .generation.MapGenerator import MapGenerator
from .generation.RoomController import RoomController
from .generation.RoomPrefabRegistry import RoomPrefabRegistry
from .level_editor.ActorRegistry import ActorRegistry
from .level_editor.LevelEditor import LevelEditor
from .support.constants import ROOM_HEIGHT, ROOM_WIDTH
from .support.Point import Point
from .world.World import World


def main():
    pygame.init()
    ActorRegistry.load_actors()

    room_registry = RoomPrefabRegistry()
    room_registry.load("./assets/rooms")

    map_generator = MapGenerator(
        max_width=50,
        max_height=50,
        sprawl_chance=0.5,
        room_prefabs=room_registry,
        max_rooms=500,
    )
    universe = Universe(map_generator)

    map_generator.generate(516)

    world = World(universe)
    universe.set_world(world)

    world.add_actor(Player(position=Point(ROOM_WIDTH / 2, ROOM_HEIGHT / 2)))

    room_controller = RoomController(room=map_generator.get_room(Point.ZERO))
    world.add_actor(room_controller)
    room_controller.initialize_room()

    room_controller.world.add_actor(MapView())

    game_loop = InteractiveGameLoop(universe)
    game_loop.run()


def start_editor():
    pygame.init()
    ActorRegistry.load_actors()

    file_path: str | None = None
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    universe = Universe(map=None)

    world = World(universe)
    universe.set_world(world)

    level_editor = LevelEditor()
    world.add_actor(level_editor)
    if file_path is not None:
        level_editor.open_file(file_path)

    game_loop = InteractiveGameLoop(universe)
    game_loop.run()


def format_room_files():
    RoomPrefabRegistry().load("./assets/rooms")
    for directory, _, files in walk("./assets/rooms", onerror=print):
        for room_path in files:
            if not room_path.endswith(".json"):
                continue
            room_path = path.join(directory, room_path)
            file_content = ""
            with open(room_path, "rt") as file:
                file_content = file.read()
            with open(room_path, "wt") as file:
                file.write(json.dumps(json.loads(file_content), indent=4, sort_keys=True))
