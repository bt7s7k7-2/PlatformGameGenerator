import gymnasium
from gymnasium.envs.registration import register

from .PgEnv import *

register(
    id="gymnasium_int/PgEnv",
    entry_point="gymnasium_int:PgEnv",
)


def main():
    env = gymnasium.make("gymnasium_int/PgEnv", render_mode="human")
    observation, info = env.reset()

    episode_over = False
    while not episode_over:
        action = env.action_space.sample()
        observation, reward, terminated, truncated, info = env.step(action)

        episode_over = terminated or truncated

    env.close()
