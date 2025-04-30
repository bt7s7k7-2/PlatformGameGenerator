from dataclasses import dataclass
from functools import cached_property
from random import random
from traceback import print_exc
from typing import ClassVar, override

import pygame

from ..actors.Player import Player
from ..actors.support.GuiRenderer import GuiRenderer
from ..game_core.Camera import CameraClient
from ..game_core.InputClient import InputClient
from ..game_core.ResourceClient import ResourceClient
from ..generation.RoomInfo import RoomInfo
from ..generation.RoomPrefab import RoomPrefab
from ..generation.RoomPrefabRegistry import RoomPrefabRegistry
from ..gui.ButtonElement import ButtonElement
from ..gui.GuiElement import GuiContainer
from ..gui.ObjectInput import ObjectInput
from ..support.Point import Axis, Point
from ..world.World import World
from .LevelSerializer import LevelSerializer


@dataclass(kw_only=True)
class TestPlayController(InputClient, GuiRenderer, ResourceClient, CameraClient):
    editor_world: "World"
    room_prefab: RoomPrefab
    spawn_position: Point

    use_info: ClassVar[bool] = False
    room_info: ClassVar[RoomInfo] = RoomInfo(0, Point.ZERO, 0).set_all_parameters(0.75)

    def rebuild(self):
        play_world = World(self.universe)

        def switch_world():
            try:
                self.universe.set_world(play_world)

                if TestPlayController.use_info:
                    RoomPrefabRegistry.load()
                    del TestPlayController.room_info.persistent_flags[:]
                    TestPlayController.room_info.seed = random()
                    self.room_prefab.instantiate_root(TestPlayController.room_info, None, play_world)
                else:
                    LevelSerializer.deserialize(play_world, self.room_prefab.data)

                player = Player()
                player.position = self.spawn_position
                play_world.add_actor(player)
                play_world.add_actor(self)
            except Exception:
                if self.world is None:  # type: ignore
                    LevelSerializer.deserialize(play_world, self.room_prefab.data)
                    player = Player()
                    player.position = self.spawn_position
                    play_world.add_actor(player)
                    play_world.add_actor(self)
                print_exc()
                self.universe.set_world(self.world)

        self.universe.queue_task(switch_world)

    @override
    def update(self, delta: float):
        was_enter_pressed = any(event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN for event in self._input.events)

        if was_enter_pressed:
            self.universe.queue_task(lambda: self.universe.set_world(self.editor_world))

    @cached_property
    def _gui(self):
        config = [
            ObjectInput(value=TestPlayController, font=self._resource_provider.font, manifest=[("use_info", bool)]),
            ObjectInput(value=TestPlayController.room_info, font=self._resource_provider.font, manifest=RoomInfo.get_manifest()),
            ButtonElement(font=self._resource_provider.font, text="Rebuild", on_click=self.rebuild),
        ]

        def toggle_config(state: bool):
            if state == False:
                del self._gui.children[1:]
                return

            self._gui.children.extend(config)  # type: ignore

        return GuiContainer(
            axis=Axis.COLUMN,
            bg_opacity=192,
            children=[
                ButtonElement(stateful=True, font=self._resource_provider.font, text="Config", on_changed=toggle_config),
            ],
        )

    @override
    def draw_gui(self):
        for event in self._input.events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.rebuild()

        self._gui.update_and_render(self._camera, self._input)
        return super().draw_gui()
