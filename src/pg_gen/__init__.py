import sys

from .actors.Player import Player
from .game_core.InteractiveGameLoop import InteractiveGameLoop
from .game_core.Universe import Universe
from .generation.MapGenerator import MapGenerator
from .generation.RoomController import RoomController
from .level_editor.ActorRegistry import ActorRegistry
from .level_editor.LevelEditor import LevelEditor
from .support.constants import ROOM_HEIGHT, ROOM_WIDTH
from .support.Point import Point
from .world.World import World


def main():
    ActorRegistry.load_actors()

    map_generator = MapGenerator(
        max_width=4,
        max_height=4,
        sprawl_chance=0.5,
    )
    universe = Universe(map_generator)

    map_generator.generate(516)

    world = World(universe)
    universe.set_world(world)

    world.add_actor(Player(position=Point(ROOM_WIDTH / 2, ROOM_HEIGHT / 2)))

    room_controller = RoomController(room=map_generator.get_room(Point.ZERO))
    world.add_actor(room_controller)
    room_controller.initialize_room()

    game_loop = InteractiveGameLoop(universe)
    game_loop.run()


def start_editor():
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
