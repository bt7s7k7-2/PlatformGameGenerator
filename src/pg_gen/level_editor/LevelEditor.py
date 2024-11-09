from dataclasses import dataclass, field
from functools import cached_property
from typing import Callable, Dict, List, Tuple

import pygame

from ..actors.Player import Player
from ..actors.support.GuiRenderer import GuiRenderer
from ..game_core.Camera import CameraClient
from ..game_core.InputClient import InputClient
from ..game_core.ResourceClient import ResourceClient
from ..generation.RoomPrefab import RoomPrefab
from ..gui.ButtonElement import ButtonElement
from ..gui.GuiElement import GuiContainer
from ..gui.ObjectInput import ObjectInput
from ..gui.SearchInput import SearchInput
from ..gui.TextInput import TextInput
from ..support.Color import Color
from ..support.constants import ROOM_HEIGHT, ROOM_WIDTH
from ..support.ObjectManifest import ObjectManifestDeserializer, ObjectManifestSerializer
from ..support.Point import Axis, Point
from ..support.support import is_intersection
from ..world.Actor import Actor
from ..world.World import World
from .ActorRegistry import ActorRegistry, ActorType
from .LevelSerializer import LevelSerializer
from .TestPlayController import TestPlayController


@dataclass
class LevelEditor(GuiRenderer, ResourceClient, InputClient, CameraClient):
    file_path: str | None = None

    _managed_actors: List[Actor] = field(init=False, default_factory=lambda: [])
    _managed_actors_types: List[ActorType] = field(init=False, default_factory=lambda: [])
    _undo_history: List[str] = field(init=False, repr=False, default_factory=lambda: [])
    _redo_history: List[str] = field(init=False, repr=False, default_factory=lambda: [])

    _selected_actor_type: ActorType | None = None
    _selected_actor: Actor | None = None
    _design_mode: bool = True
    _drag_callback: Callable[[Point], None] | None = None
    _aux_data: Dict = field(default_factory=lambda: {})
    _prefab: RoomPrefab | None = None

    def on_added(self):
        self.world.paused = True

    @cached_property
    def _gui(self):
        def update(value: bool):
            if value:
                self._gui.children[1] = self._get_manifest_gui()
            else:
                self._gui.children[1] = self._get_search_gui()

        return GuiContainer(
            offset=Point(10, 10),
            bg_opacity=192,
            axis=Axis.COLUMN,
            children=[
                ButtonElement(font=self._resource_provider.font, text="Config", stateful=True, on_changed=update),
                self._get_search_gui(),
            ],
        )

    def _get_manifest_gui(self):
        if self._prefab is None:
            self._prefab = RoomPrefab(name="", data="")
        return ObjectInput(offset=Point(10, 10), value=self._prefab, manifest=RoomPrefab.get_manifest(), font=self._resource_provider.font, on_changed=self.handle_file_changed)

    def _get_search_gui(self):
        return SearchInput(
            search=TextInput(font=self._resource_provider.font, selected=True, always_selected=True),
            axis=Axis.COLUMN,
            search_function=ActorRegistry.get_actor_types,
            get_label=lambda v: v[0],
            on_changed=lambda v: setattr(self, "_selected_actor_type", v[1] if v is not None else None),
            max_results=5,
        )

    def draw_gui(self):
        surface = self._camera.screen

        vertical_guide_size = Point(1, ROOM_HEIGHT * self._camera.zoom)
        vertical_guide_center = self._camera.world_to_screen(Point(ROOM_WIDTH / 2, 0))
        one_tile = self._camera.zoom
        self._camera.draw_placeholder_raw(vertical_guide_center - Point(one_tile, 0), vertical_guide_size, Color.WHITE, 127)
        self._camera.draw_placeholder_raw(vertical_guide_center + Point(one_tile, 0), vertical_guide_size, Color.WHITE, 127)

        horizontal_guide_size = Point(ROOM_WIDTH * self._camera.zoom, 1)
        horizontal_guide_start = self._camera.world_to_screen(Point(0, 2))

        self._camera.draw_placeholder_raw(horizontal_guide_start, horizontal_guide_size, Color.WHITE, 127)
        self._camera.draw_placeholder_raw(horizontal_guide_start + Point(0, one_tile * 2), horizontal_guide_size, Color.WHITE, 127)

        if self._selected_actor is not None:
            for position, size, _ in self.get_selection_handles():
                pygame.draw.rect(
                    surface,
                    Color.YELLOW.to_pygame_color(),
                    position.to_pygame_rect(size),
                    width=1,
                )

                pygame.draw.rect(
                    surface,
                    Color.BLACK.to_pygame_color(),
                    (position + Point(1, 1)).to_pygame_rect(size - Point(2, 2)),
                    width=1,
                )

        self._gui.update_and_render(self._camera, self._input)

    def spawn_actor(self, actor_type: ActorType, position: Point):
        actor = actor_type.create_instance()
        position -= actor.size * 0.5
        actor.position = position.quantize(0.5)
        self.world.add_actor(actor)
        self.add_managed_actor(actor, actor_type)
        self._selected_actor = actor
        return actor

    def add_managed_actor(self, actor: Actor, actor_type: ActorType):
        self._managed_actors.append(actor)
        self._managed_actors_types.append(actor_type)

    def start_drag(self, init_pos: Point, callback: Callable[[Point], None]):
        pass

    def create_resize_callback(self, direction: Point):
        axis = direction.abs()
        is_negative = direction.is_negative()

        def callback(start_pos: Point):
            assert self._selected_actor is not None
            target = self._selected_actor

            start_world_pos = target.position
            start_world_size = target.size

            def on_drag(mouse_pos: Point):
                delta = mouse_pos - start_pos
                world_delta = delta * (1 / self._camera.zoom)
                world_delta *= axis

                if not is_negative:
                    target.size = (start_world_size + world_delta).quantize(0.5)
                    target.position = start_world_pos
                else:
                    target.size = (start_world_size - world_delta).quantize(0.5)
                    target.position = (start_world_pos + world_delta).quantize(0.5)

                if target.size.is_negative():
                    target.position += target.size * axis
                    target.size += target.size * axis * -2

            return on_drag

        return callback

    def create_move_callback(self):
        def callback(start_pos: Point):
            assert self._selected_actor is not None
            target = self._selected_actor
            start_world_pos = target.position

            def on_drag(mouse_pos: Point):
                delta = mouse_pos - start_pos
                world_delta = delta * (1 / self._camera.zoom)
                new_position = start_world_pos + world_delta
                new_position = new_position.quantize(0.5)
                target.position = new_position
                pass

            return on_drag

        return callback

    def get_selection_handles(self) -> List[Tuple[Point, Point, Callable[[Point], Callable[[Point], None]]]]:
        if self._selected_actor is None:
            return []

        handle_size = Point.ONE * 10
        selected = self._selected_actor
        position = selected.position * self._camera.zoom
        size = selected.size * self._camera.zoom
        center_offset = size * 0.5
        center = position + center_offset

        return [
            *(
                (center + offset - handle_size * 0.5, handle_size, self.create_resize_callback(offset.normalize()))
                for offset in [center_offset.right(), center_offset.right() * -1, center_offset.down(), center_offset.down() * -1]
            ),
            (position, size, self.create_move_callback()),
        ]

    def get_save_data(self, aux_data: Dict):
        return LevelSerializer.serialize(self._managed_actors, self._managed_actors_types, aux_data)

    def apply_save_data(self, raw_data: str):
        for actor in self._managed_actors:
            actor.remove()

        self._managed_actors.clear()
        self._managed_actors_types.clear()

        aux_data = LevelSerializer.deserialize(self.world, raw_data, spawn_callback=self.add_managed_actor)

        return aux_data

    def push_undo_stack(self):
        self._create_history_entry(self._undo_history)
        self._redo_history.clear()

    def handle_file_changed(self):
        if self.file_path is not None:
            with open(self.file_path, "wt") as file:
                if self._prefab is not None:
                    self._aux_data = {"$config": ObjectManifestSerializer.serialize(self._prefab, RoomPrefab.get_manifest())}
                file.write(self.get_save_data(self._aux_data))

    def open_file(self, file_path: str):
        self.file_path = file_path
        try:
            with open(self.file_path, "rt") as file:
                raw_data = file.read()
                self._aux_data = self.apply_save_data(raw_data)
                if "$config" in self._aux_data:
                    self._prefab = ObjectManifestDeserializer.deserialize(self._aux_data["$config"], RoomPrefab(name="", data=""), RoomPrefab.get_manifest())
                    pass
        except FileNotFoundError:
            # If the level file is not found we are creating a new level, we can keep the current, empty, state
            pass

    def _create_history_entry(self, target: List[str]):
        selected_index = self._managed_actors.index(self._selected_actor) if self._selected_actor is not None else None
        state = self.get_save_data({"selected_index": selected_index})
        target.append(state)

    def _apply_history_entry(self, target: List[str]):
        if len(target) == 0:
            return False

        state = target.pop()
        data = self.apply_save_data(state)
        selected_index = data["selected_index"]
        if isinstance(selected_index, int):
            self._selected_actor = self._managed_actors[selected_index]

        return True

    def undo(self):
        self._create_history_entry(self._redo_history)
        if not self._apply_history_entry(self._undo_history):
            # Undo operation failed, revert change to redo history
            self._redo_history.pop()

    def redo(self):
        self._create_history_entry(self._undo_history)
        if not self._apply_history_entry(self._redo_history):
            # Redo operation failed, revert change to undo history
            self._undo_history.pop()

    def test_play(self):
        play_world = World(self.universe)
        x, y = pygame.mouse.get_pos()

        def switch_world():
            self.universe.set_world(play_world)

            LevelSerializer.deserialize(play_world, LevelSerializer.serialize(self._managed_actors, self._managed_actors_types, {}))
            player = Player()
            player.position = Point(x, y) * (1 / self._camera.zoom) - player.size * 0.5
            play_world.add_actor(player)
            play_world.add_actor(TestPlayController(editor_world=self.world))

        self.universe.queue_task(switch_world)

    def update(self, delta: float):
        for event in self._input.events:
            if event.type == pygame.KEYDOWN:
                is_ctrl = self._input.keys[pygame.K_LCTRL]
                is_shift = self._input.keys[pygame.K_LSHIFT]

                if event.key == pygame.K_DELETE:
                    if self._selected_actor is None:
                        continue
                    # Deleting actor
                    self.push_undo_stack()
                    actor_to_delete = self._selected_actor
                    self._selected_actor = None
                    index = self._managed_actors.index(actor_to_delete)
                    self._managed_actors.pop(index)
                    self._managed_actors_types.pop(index)
                    actor_to_delete.remove()
                    self.handle_file_changed()
                elif event.key == pygame.K_z and is_ctrl and is_shift:
                    self.redo()
                    self.handle_file_changed()
                elif event.key == pygame.K_z and is_ctrl:
                    self.undo()
                    self.handle_file_changed()
                elif event.key == pygame.K_RETURN:
                    self.test_play()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                mouse_position = Point(x, y)
                if event.button == pygame.BUTTON_RIGHT:
                    if self._selected_actor_type is None:
                        continue
                    # Spawning actor
                    self.push_undo_stack()
                    self.spawn_actor(self._selected_actor_type, mouse_position * (1 / self._camera.zoom))
                    self.handle_file_changed()
                elif event.button == pygame.BUTTON_LEFT:
                    for position, size, callback_factory in self.get_selection_handles():
                        if is_intersection(mouse_position, Point.ZERO, position, size):
                            # Clicked on a selection handle, begin its function
                            self.push_undo_stack()
                            self._drag_callback = callback_factory(mouse_position)
                            break
                    else:
                        mouse_world_position = mouse_position * (1 / self._camera.zoom)
                        for actor in self._managed_actors:
                            if is_intersection(mouse_world_position, Point.ZERO, actor.position, actor.size):
                                # Did click on actor, select
                                self.push_undo_stack()
                                self._selected_actor = actor
                                break
                        else:
                            # Did not click on any actors, unselect if any
                            if self._selected_actor is not None:
                                self.push_undo_stack()
                                self._selected_actor = None
            elif event.type == pygame.MOUSEMOTION:
                if self._drag_callback is None:
                    continue
                x, y = event.pos
                self._drag_callback(Point(x, y))
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT:
                    self._drag_callback = None
                    self.handle_file_changed()

        if self._selected_actor is not None and self._selected_actor.world is None:
            self._selected_actor = None
