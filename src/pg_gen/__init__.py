from pygame.locals import *

from .entities.Wall import Wall
from .game_core.InteractiveGameLoop import InteractiveGameLoop
from .game_core.Universe import Universe
from .support.Point import Point
from .world.World import World


def main():
    universe = Universe()
    world = World(universe)
    universe.world = world

    world.add_entity(
        Wall(
            world,
            universe,
            position=Point.ONE * 100,
            size=Point.ONE * 100,
        )
    )

    game_loop = InteractiveGameLoop(universe)
    game_loop.run()
