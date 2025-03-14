from dataclasses import astuple
from typing import Literal, override

import numpy as np
import pygame
from gymnasium import Env, spaces

from pg_gen.actors.Player import Player
from pg_gen.game_core.GameLoop import GameLoop
from pg_gen.game_core.InputState import InputState
from pg_gen.game_core.InteractiveGameLoop import InteractiveGameLoop
from pg_gen.game_core.Universe import Universe
from pg_gen.generation.RoomController import RoomController
from pg_gen.generation.RoomInfo import RoomInfo
from pg_gen.generation.RoomPrefabRegistry import RoomPrefabRegistry
from pg_gen.level_editor.ActorRegistry import ActorRegistry
from pg_gen.support.constants import CAMERA_SCALE, ROOM_FOLDER, ROOM_HEIGHT, ROOM_WIDTH
from pg_gen.support.Point import Point

RenderMode = Literal["human"] | Literal["rgb_array"] | None


class PgEnv(Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 25}

    @property
    def time_per_frame(self):
        return 1 / self.metadata["render_fps"]

    def __init__(self, render_mode: RenderMode = "rgb_array"):
        self.window_size = 512  # The size of the PyGame window

        self.observation_space = spaces.Dict(
            {"agent": spaces.Box(low=0, high=max(ROOM_WIDTH, ROOM_HEIGHT), shape=(2,), dtype=np.float64), "score": spaces.Box(low=0, high=10000, shape=(1,), dtype=np.int32)}
        )

        self._action_to_direction = ["right", "up", "left", "down", "jump"]
        self.action_space = spaces.MultiBinary(len(self._action_to_direction))

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode: RenderMode = render_mode  # type: ignore

        self.universe: Universe | None = None
        self.game_loop: GameLoop | None = None
        self.terminated = False
        self.last_score = 0

    def _get_obs(self):
        assert self.universe is not None
        player = self.universe.di.inject(Player)

        return {
            "agent": np.array([*astuple(player.position)], dtype=np.float64),
            "score": np.array([player.score], dtype=np.int32),
        }

    def _get_info(self):
        return {}

    @override
    def reset(self, seed=None, options=None):  # type: ignore
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        self.terminated = False

        ActorRegistry.load_actors()
        RoomPrefabRegistry.load(ROOM_FOLDER)

        room_info = RoomInfo(1, Point.ZERO, 0, RoomPrefabRegistry.find_rooms("empty_room", None, None)[0])

        self.universe = Universe()

        room = RoomController.initialize_and_activate(self.universe, room_info)
        world = room.world
        world.add_actor(Player(position=Point(2, 2)))
        self.universe.set_world(world)

        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()

        return observation, info

    @override
    def step(self, action):
        assert self.universe is not None

        input_state = self.universe.di.inject(InputState)
        input_state.clear()
        for index, name in enumerate(self._action_to_direction):
            action_value = action[index]
            input_state.__setattr__(name, True if action_value else False)

        terminated = self.terminated

        observation = self._get_obs()

        reward = 0 if terminated else 1
        score = float(observation["score"])
        reward += score - self.last_score
        self.last_score = score

        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()

        return observation, reward, terminated, False, info

    @override
    def render(self):
        if self.render_mode == "rgb_array":
            return self._render_frame()

    def _render_frame(self):
        assert self.universe is not None

        if self.render_mode == "human":
            pygame.init()
            if self.game_loop is None:
                self.game_loop = InteractiveGameLoop(self.universe)
                self.game_loop.allow_termination = False
                self.game_loop.disable_input_clearing = True

            assert isinstance(self.game_loop, InteractiveGameLoop)
            self.terminated = self.game_loop.handle_input()
            self.game_loop.update_and_render(self.time_per_frame)
            pygame.display.update()
            self.game_loop.fps_keeper.tick(self.metadata["render_fps"])
        elif self.render_mode == "rgb_array":
            if self.game_loop is None:
                pygame.init()
                surface = pygame.display.set_mode((CAMERA_SCALE * ROOM_WIDTH, CAMERA_SCALE * ROOM_HEIGHT))
                self.game_loop = GameLoop(surface, self.universe)

            self.game_loop.update_and_render(self.time_per_frame)

            return np.transpose(
                pygame.surfarray.pixels3d(self.game_loop.surface),
                axes=(1, 0, 2),
            )
