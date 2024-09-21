from pygame.locals import *

from .entities.Player import Player
from .entities.Wall import Wall
from .game_core.InteractiveGameLoop import InteractiveGameLoop
from .game_core.Universe import Universe
from .support.Point import Point
from .world.World import World


def main():
    universe = Universe()
    world = World(universe)
    universe.world = world

    world.add_actor(
        Wall(
            universe,
            position=Point(0, 19),
            size=Point(20, 1),
        )
    )

    world.add_actor(
        Wall(
            universe,
            position=Point(10, 17),
            size=Point(1, 2),
        )
    )

    world.add_actor(
        Wall(
            universe,
            position=Point(14, 14),
            size=Point(3, 1),
        )
    )

    world.add_actor(
        Wall(
            universe,
            position=Point(9, 11),
            size=Point(3, 1),
        )
    )

    world.add_actor(
        Wall(
            universe,
            position=Point(4, 8),
            size=Point(3, 1),
        )
    )

    world.add_actor(
        Wall(
            universe,
            position=Point(9, 5),
            size=Point(3, 1),
        )
    )

    world.add_actor(
        Player(
            universe,
            position=Point.ONE * 2,
        )
    )

    game_loop = InteractiveGameLoop(universe)
    game_loop.run()
