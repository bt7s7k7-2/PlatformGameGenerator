import json
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from traceback import print_exc
from typing import Callable, Dict, List, Tuple

import pygame

from ..actors.support.ConfigurableObject import ConfigurableObject
from ..actors.support.GuiRenderer import GuiRenderer
from ..game_core.Camera import CameraClient
from ..game_core.InputClient import InputClient
from ..game_core.ResourceClient import ResourceClient
from ..generation.RoomInfo import RoomInfo
from ..generation.RoomPrefab import RoomPrefab
from ..gui.ButtonElement import ButtonElement
from ..gui.GuiElement import GuiContainer
from ..gui.ObjectInput import ObjectInput
from ..gui.SearchInput import SearchInput
from ..gui.TextInput import TextInput
from ..support.Color import Color
from ..support.constants import HIGHLIGHT_2_COLOR, ROOM_HEIGHT, ROOM_WIDTH, TEXT_BG_COLOR, TEXT_COLOR
from ..support.ObjectManifest import ObjectManifest, ObjectManifestDeserializer, ObjectManifestSerializer
from ..support.Point import Axis, Point
from ..support.support import is_intersection
from ..world.Actor import Actor
from ..world.World import World
from .ActorRegistry import ActorRegistry, ActorType
from .LevelSerializer import LevelSerializer
from .TestPlayController import TestPlayController


class LevelEditorType(Enum):
    NORMAL = 0
    SOCKET = 1


_manifest: ObjectManifest = [
    ("type", LevelEditorType),
]


@dataclass
class LevelEditor(GuiRenderer, ResourceClient, InputClient, CameraClient):
    file_path: str | None = None
    type: LevelEditorType = LevelEditorType.NORMAL

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
    _object_config_gui: TextInput | None = None

    _editor_config: dict = field(default_factory=lambda: {})
    _config_init = False

    def __post_init__(self):
        try:
            with open("./editor_config.json", "rt") as file:
                config = json.load(file)
                self._editor_config = config
        except Exception:
            print_exc()
            pass

    def save_config(self):
        ObjectManifestSerializer.serialize(self, _manifest, self.get_config())

        with open("./editor_config.json", "wt") as file:
            json.dump(self._editor_config, file)

    def get_config(self) -> dict:
        return self._editor_config.setdefault(self.file_path, {})

    def on_added(self):
        self.world.paused = True
        if self._config_init:
            room = ObjectManifestSerializer.serialize(TestPlayController.room_info, RoomInfo.get_manifest())
            room["use_info"] = TestPlayController.use_info
            self.get_config()["room"] = room
            self.save_config()
        else:
            config = self.get_config()

            try:
                room = config["room"]
                ObjectManifestDeserializer.deserialize(room, TestPlayController.room_info, RoomInfo.get_manifest())
                TestPlayController.use_info = room["use_info"]
            except Exception:
                print_exc()
                pass

            try:
                ObjectManifestDeserializer.deserialize(config, self, _manifest)
            except Exception:
                print_exc()
            else:
                self._apply_type()

            self._config_init = True

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
        return GuiContainer(
            axis=Axis.COLUMN,
            offset=Point(10, 10),
            children=[
                ObjectInput(value=self, manifest=_manifest, font=self._resource_provider.font, on_changed=lambda: self._apply_type() or self.save_config()),
                ObjectInput(value=self._prefab, manifest=RoomPrefab.get_manifest(), font=self._resource_provider.font, on_changed=self.handle_file_changed),
            ],
        )

    def _apply_type(self):
        if self.type == LevelEditorType.NORMAL:
            self._camera.offset = Point.ZERO
        else:
            self._camera.offset = Point(-1, -1)

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
        horizontal_guide_size = Point(ROOM_WIDTH * self._camera.zoom, 1)
        one_tile = self._camera.zoom

        if self.type == LevelEditorType.NORMAL:
            vertical_guide_center = self._camera.world_to_screen(Point(ROOM_WIDTH / 2, 0))
            self._camera.draw_placeholder_raw(vertical_guide_center - Point(one_tile, 0), vertical_guide_size, Color.WHITE, 127)
            self._camera.draw_placeholder_raw(vertical_guide_center + Point(one_tile, 0), vertical_guide_size, Color.WHITE, 127)

            horizontal_guide_start = self._camera.world_to_screen(Point(0, 2))

            self._camera.draw_placeholder_raw(horizontal_guide_start, horizontal_guide_size, Color.WHITE, 127)
            self._camera.draw_placeholder_raw(horizontal_guide_start + Point(0, one_tile * 2), horizontal_guide_size, Color.WHITE, 127)
        elif self.type == LevelEditorType.SOCKET:
            x_min, x_max = 1, ROOM_WIDTH - 1
            y_min, y_max = 1, ROOM_HEIGHT - 1

            for x in [x_min, (x_min + x_max) // 2, x_max]:
                self._camera.draw_placeholder_raw(Point(one_tile * x, 0), vertical_guide_size, Color.WHITE, 127)

            for y in [y_min, y_max]:
                self._camera.draw_placeholder_raw(Point(0, y * one_tile), horizontal_guide_size, Color.WHITE, 127)

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

            if isinstance(self._selected_actor, ConfigurableObject):
                if self._object_config_gui is None:
                    self._object_config_gui = TextInput(selected=True, always_selected=True, font=self._resource_provider.font, placeholder="Config", on_changed=self._update_configurable)
                    self._object_config_gui.value = self._selected_actor.config

                self._object_config_gui.offset = self._camera.world_to_screen(self._selected_actor.position)

                if self._object_config_gui.value != self._selected_actor.config:
                    self._object_config_gui.value = self._selected_actor.config
            else:
                self._object_config_gui = None
        else:
            self._object_config_gui = None

        for actor in self._managed_actors:
            if actor != self._selected_actor and isinstance(actor, ConfigurableObject):
                self._resource_provider.font.render_to(self._camera.screen, self._camera.world_to_screen(actor.position).to_pygame_coordinates(), actor.config, TEXT_COLOR, TEXT_BG_COLOR)

        if self._object_config_gui is not None:
            self._object_config_gui.update_and_render(self._camera, self._input)
        else:
            self._gui.update_and_render(self._camera, self._input)

    def _update_configurable(self, config: str):
        assert isinstance(self._selected_actor, ConfigurableObject)
        assert self._object_config_gui is not None
        valid = self._selected_actor.apply_config(config)

        if valid:
            self._object_config_gui.color = TEXT_COLOR
        else:
            self._object_config_gui.color = HIGHLIGHT_2_COLOR

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
        position = self._camera.world_to_screen(selected.position)
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
                if self._prefab is None:
                    self._prefab = RoomPrefab(name="", data="")
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

    def duplicate(self):
        actor = self._selected_actor
        if actor is None:
            return
        index = self._managed_actors.index(actor)
        type = self._managed_actors_types[index]
        copy = type.create_instance()
        copy.position = actor.position
        copy.size = actor.size
        if isinstance(actor, ConfigurableObject):
            assert isinstance(copy, ConfigurableObject)
            copy.apply_config(actor.config)
        self.add_managed_actor(copy, type)
        self._selected_actor = copy

    def test_play(self):
        play_world = World(self.universe)
        spawn_position = Point(*pygame.mouse.get_pos()) * (1 / self._camera.zoom) - Point(0.5, 0.5)
        if self._prefab is None:
            self._prefab = RoomPrefab(name="", data="")

        self._prefab.data = self.get_save_data({})
        test_controller = TestPlayController(self.universe, editor_world=self.world, room_prefab=self._prefab, spawn_position=spawn_position)
        test_controller.rebuild()

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
                elif event.key == pygame.K_d and is_ctrl:
                    self.duplicate()
                    self.handle_file_changed()
                elif event.key == pygame.K_z and is_ctrl and is_shift:
                    self.redo()
                    self.handle_file_changed()
                elif event.key == pygame.K_z and is_ctrl:
                    self.undo()
                    self.handle_file_changed()
                elif event.key == pygame.K_RETURN:
                    self.test_play()
                elif event.key == pygame.K_PAGEUP or event.key == pygame.K_PAGEDOWN:
                    print(event.key)
                    if self._selected_actor is None:
                        continue

                    index = self._managed_actors.index(self._selected_actor)
                    self.push_undo_stack()
                    self._managed_actors.pop(index)
                    self._selected_actor.remove()
                    type = self._managed_actors_types.pop(index)

                    in_front = event.key == pygame.K_PAGEUP

                    if in_front:
                        self._managed_actors.insert(0, self._selected_actor)
                        self._managed_actors_types.insert(0, type)
                    else:
                        self._managed_actors.append(self._selected_actor)
                        self._managed_actors_types.append(type)

                    self.world.add_actor(self._selected_actor, in_front=in_front)
                    self.handle_file_changed()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                mouse_position = Point(x, y)
                if event.button == pygame.BUTTON_RIGHT:
                    if self._selected_actor_type is None:
                        continue
                    # Spawning actor
                    self.push_undo_stack()
                    self.spawn_actor(self._selected_actor_type, self._camera.screen_to_world(mouse_position))
                    self.handle_file_changed()
                elif event.button == pygame.BUTTON_LEFT:
                    for position, size, callback_factory in self.get_selection_handles():
                        if is_intersection(mouse_position, Point.ZERO, position, size):
                            # Clicked on a selection handle, begin its function
                            self.push_undo_stack()
                            self._drag_callback = callback_factory(mouse_position)
                            break
                    else:
                        mouse_world_position = self._camera.screen_to_world(mouse_position)
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
