import json
import sys
from os import path, walk

import pygame

from .actors.Player import Player
from .debug.MapView import MapView
from .difficulty.DifficultyOptimizer import DifficultyOptimizer
from .game_core.InteractiveGameLoop import InteractiveGameLoop
from .game_core.Universe import Universe
from .generation.Requirements import Requirements
from .generation.RoomController import RoomController
from .generation.RoomPrefabRegistry import RoomPrefabRegistry
from .level_editor.ActorRegistry import ActorRegistry
from .level_editor.LevelEditor import LevelEditor
from .support.constants import ROOM_FOLDER, ROOM_HEIGHT, ROOM_WIDTH
from .support.Point import Point
from .world.World import World


def main():
    pygame.init()
    ActorRegistry.load_actors()

    RoomPrefabRegistry.load(ROOM_FOLDER)

    requirements = Requirements(
        seed=62911,
        max_width=50,
        max_height=50,
        sprawl_chance=0.5,
        max_rooms=100,
    )

    requirements.parameter_chances.set_all_parameters(0.75)

    universe = Universe()

    optimizer = DifficultyOptimizer(universe, requirements)
    map = optimizer.achieve_target_difficulty()
    universe.map = map

    room_controller = RoomController.initialize_and_activate(universe, map.get_room(Point.ZERO), None)
    room_controller.world.add_actor(MapView())
    room_controller.world.add_actor(Player(position=Point(ROOM_WIDTH / 2, ROOM_HEIGHT / 2)))

    game_loop = InteractiveGameLoop(universe)
    game_loop.run()


def start_editor():
    pygame.init()
    ActorRegistry.load_actors()

    file_path: str | None = None
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    universe = Universe()

    world = World(universe)
    universe.set_world(world)

    game_loop = InteractiveGameLoop(universe)

    level_editor = LevelEditor(file_path=file_path)
    world.add_actor(level_editor)
    if file_path is not None:
        level_editor.open_file(file_path)

    game_loop.run()


def format_room_files():
    RoomPrefabRegistry.load("./assets/rooms")
    for directory, _, files in walk("./assets/rooms", onerror=print):
        for room_path in files:
            if not room_path.endswith(".json"):
                continue
            room_path = path.join(directory, room_path)
            file_content = ""
            with open(room_path, "rt") as file:
                file_content = file.read()
            with open(room_path, "wt") as file:
                file.write(json.dumps(json.loads(file_content), indent=4, sort_keys=True) + "\n")
