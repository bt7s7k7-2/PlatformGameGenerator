import json
import sys
from itertools import chain, pairwise
from os import path, walk
from random import Random
from time import perf_counter
from traceback import print_exc

import pygame

from .actors.Player import Player
from .debug.MapView import MapView
from .difficulty.DifficultyOptimizer import DifficultyOptimizer
from .difficulty.LevelSolver import LevelSolver, LevelSolverState
from .game_core.InteractiveGameLoop import InteractiveGameLoop
from .game_core.Universe import Universe
from .generation.RoomController import RoomController
from .generation.RoomParameter import UNUSED_PARAMETER, RoomParameter, RoomParameterCollection
from .generation.RoomPrefabRegistry import RoomPrefabRegistry
from .level_editor.ActorRegistry import ActorRegistry
from .level_editor.LevelEditor import LevelEditor
from .support.Color import Color
from .support.constants import ROOM_FOLDER, ROOM_HEIGHT, ROOM_WIDTH
from .support.Point import Point
from .world.World import World


def main():
    pygame.init()
    ActorRegistry.load_actors()

    RoomPrefabRegistry.load(ROOM_FOLDER)

    universe = Universe()

    target_difficulty = RoomParameterCollection()
    target_difficulty.set_all_parameters(UNUSED_PARAMETER)
    target_difficulty.set_parameter(RoomParameter.REWARD, 500)
    target_difficulty.set_parameter(RoomParameter.JUMP, 10)
    target_difficulty.set_parameter(RoomParameter.ENEMY, 100)
    target_difficulty.set_parameter(RoomParameter.SPRAWL, 50)
    optimizer = DifficultyOptimizer(universe, target_difficulty=target_difficulty, random=Random(108561))

    start = perf_counter()
    optimizer.initialize_population()
    optimizer.optimize()
    end = perf_counter()
    print(f"Optimization took: {(end-start)*1000:.2f} ms")

    best_candidate = optimizer.get_best_candidate()
    print(f"Best candidate: {optimizer.get_best_difficulty()} {best_candidate.requirements}")
    map = best_candidate.get_map()
    universe.map = map

    def map_click_callback(button: int, position: Point):
        if button != pygame.BUTTON_LEFT:
            return
        room_controller = map_view.room_controller
        if room_controller is None:
            return
        room_controller.switch_rooms_absolute(None, position)
        pass

    room_controller = RoomController.initialize_and_activate(universe, map.get_room(Point.ZERO), None)
    map_view = MapView(click_callback=map_click_callback)
    room_controller.world.add_actor(map_view)

    solution = best_candidate.solution
    assert solution is not None
    for i, path in enumerate(solution.steps):
        add_annotation_for_path(map_view, path, i)

    room_controller.world.add_actor(Player(position=Point(ROOM_WIDTH / 2, ROOM_HEIGHT / 2)))

    if len(sys.argv) > 1 and sys.argv[1] == "only-generate":
        sys.exit(0)

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


_path_colors = [Color.GREEN, Color.CYAN, Color.MAGENTA, Color.WHITE, Color.ORANGE]


def add_annotation_for_path(map_view: MapView, path: list[Point], index: int):
    for node, next in pairwise(chain(path, [path[-1]])):
        label = str(index)
        if node == path[0]:
            label += "^"
        elif node == path[-1]:
            label += "*"
        map_view.add_annotation(node, label, _path_colors[index % len(_path_colors)])

        if next == node:
            continue

        vector = next - node
        map_view.add_annotation(node, ((index % 10) - 5, vector.as_direction()), _path_colors[index % len(_path_colors)])


def test_pathfinding():
    pygame.init()
    ActorRegistry.load_actors()

    RoomPrefabRegistry.load(ROOM_FOLDER)

    universe = Universe()

    target_difficulty = RoomParameterCollection()
    target_difficulty.set_all_parameters(UNUSED_PARAMETER)
    optimizer = DifficultyOptimizer(universe, target_difficulty, Random(108560), max_population=1)

    optimizer.get_parameter("max_rooms").override_value(100)
    optimizer.get_parameter("max_width").override_value(100)
    optimizer.get_parameter("max_height").override_value(100)

    optimizer.initialize_population()
    best_candidate = optimizer.get_best_candidate()
    map = best_candidate.get_map()
    universe.map = map

    viewer_world = World(universe)

    start: Point | None = None
    end: Point | None = None

    def click_callback(button: int, position: Point):
        nonlocal start, end

        if button == pygame.BUTTON_LEFT:
            start = position
        elif button == pygame.BUTTON_RIGHT:
            end = position
        else:
            return

        map_view.clear_annotations()
        if start is not None:
            map_view.add_annotation(start, "Start", Color.CYAN)

        if end is not None:
            map_view.add_annotation(end, "End", Color.ORANGE)

        if start is not None and end is not None:
            state = LevelSolverState(position=start)
            level_solver = LevelSolver(map, best_candidate.get_path_finder())
            try:
                state = level_solver.solve_path(state, end)
                assert state is not None
                for i, step in enumerate(state.steps):
                    add_annotation_for_path(map_view, step, i)
            except AssertionError:
                print_exc()
                print("!! Failed to find path")

    map_view = MapView(
        always_show=True,
        click_callback=click_callback,
    )
    viewer_world.add_actor(map_view)

    universe.set_world(viewer_world)

    solution = best_candidate.solution
    assert solution is not None
    for i, path in enumerate(solution.steps):
        add_annotation_for_path(map_view, path, i)

    game_loop = InteractiveGameLoop(universe)
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
