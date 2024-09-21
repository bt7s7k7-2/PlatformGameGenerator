from pygame.locals import *

from .game_core.InteractiveGameLoop import InteractiveGameLoop
from .game_core.Universe import Universe
from .generation.MapGenerator import MapGenerator
from .generation.RoomController import RoomController
from .support.Point import Point
from .world.World import World


def main():
    map_generator = MapGenerator(
        max_width=4,
        max_height=4,
        sprawl_chance=0.5,
    )
    universe = Universe(map_generator)

    map_generator.generate(512)

    world = universe.world = World(universe)

    world.add_actor(RoomController(universe, room=map_generator.get_room(Point.ZERO)))

    game_loop = InteractiveGameLoop(universe)
    game_loop.run()
