from random import Random

import gymnasium
import pygame
from gymnasium.envs.registration import register

from pg_gen.difficulty.DifficultyOptimizer import DifficultyOptimizer
from pg_gen.difficulty.DifficultyReport import DifficultyReport
from pg_gen.game_core.Universe import Universe
from pg_gen.generation.RoomParameter import UNUSED_PARAMETER, RoomParameter
from pg_gen.generation.RoomPrefabRegistry import RoomPrefabRegistry
from pg_gen.level_editor.ActorRegistry import ActorRegistry
from pg_gen.support.constants import ROOM_FOLDER

from .PgEnv import PgEnv

register(
    id="gymnasium_int/PgEnv",
    entry_point=PgEnv,  # type: ignore
)


def main():
    pygame.init()
    pygame.display.init()

    ActorRegistry.load_actors()
    RoomPrefabRegistry.load(ROOM_FOLDER)

    def generate_level(universe: Universe):
        target_difficulty = DifficultyReport()
        target_difficulty.set_all_parameters(UNUSED_PARAMETER)
        target_difficulty.set_parameter(RoomParameter.REWARD, 500)
        target_difficulty.set_parameter(RoomParameter.JUMP, 10)
        target_difficulty.set_parameter(RoomParameter.ENEMY, 100)
        target_difficulty.set_parameter(RoomParameter.SPRAWL, 50)

        optimizer = DifficultyOptimizer(universe, target_difficulty=target_difficulty, random=Random(108561))

        optimizer.initialize_population()
        optimizer.optimize()

        best_candidate = optimizer.get_best_candidate()
        return best_candidate.get_map()

    env = gymnasium.make("gymnasium_int/PgEnv", render_mode="rgb_array", level=generate_level)
    observation, info = env.reset()

    if env.render_mode == "rgb_array":
        pygame.display.set_mode((1, 1), flags=pygame.HIDDEN)

    episode_over = False
    while not episode_over:
        action = env.action_space.sample()
        observation, reward, terminated, truncated, info = env.step(action)

        episode_over = terminated or truncated
        print(action, observation, info, reward)

    env.close()
