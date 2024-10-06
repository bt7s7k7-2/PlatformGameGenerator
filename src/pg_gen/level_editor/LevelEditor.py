from dataclasses import astuple, dataclass, field
from typing import Callable, Dict, List, Tuple

import pygame
from pygame import Surface

from ..entities.GuiElement import GuiElement
from ..entities.Player import Player
from ..game_core.InputClient import InputClient
from ..game_core.ResourceClient import ResourceClient
from ..support.Color import Color
from ..support.constants import CAMERA_SCALE, HIGHLIGHT_1_COLOR, TEXT_BG_COLOR, TEXT_COLOR
from ..support.Point import Point
from ..support.support import is_intersection
from ..support.TextInput import TextInput
from ..world.Actor import Actor
from ..world.World import World
from .ActorRegistry import ActorRegistry, ActorType
from .LevelSerializer import LevelSerializer
from .TestPlayController import TestPlayController


@dataclass
class LevelEditor(GuiElement, ResourceClient, InputClient):
    file_path: str | None = None

    _text_input: TextInput = field(init=False, repr=False, default_factory=lambda: TextInput())
    _search_results: List[ActorType] = field(init=False, repr=False, default_factory=lambda: [])
    _managed_actors: List[Actor] = field(init=False, default_factory=lambda: [])
    _managed_actors_types: List[ActorType] = field(init=False, default_factory=lambda: [])
    _undo_history: List[str] = field(init=False, repr=False, default_factory=lambda: [])
    _redo_history: List[str] = field(init=False, repr=False, default_factory=lambda: [])

    _selected_actor_type: ActorType | None = None
    _selected_actor: Actor | None = None
    _design_mode: bool = True
    _drag_callback: Callable[[Point], None] | None = None
    _aux_data: Dict = field(default_factory=lambda: {})

    def draw_gui(self, surface: Surface):
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

        start = Point(10, 10)
        line_offset = Point(0, 12)
        self._text_input.draw(self._resource_provider.font, surface, start)
        start += line_offset

        for type in self._search_results:
            self._resource_provider.font.render_to(
                surface,
                dest=astuple(start),
                text=type.name,
                fgcolor=HIGHLIGHT_1_COLOR if type == self._selected_actor_type else TEXT_COLOR,
                bgcolor=TEXT_BG_COLOR,
            )

            start += line_offset

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
                world_delta = delta * (1 / CAMERA_SCALE)
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
                world_delta = delta * (1 / CAMERA_SCALE)
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
        position = selected.position * CAMERA_SCALE
        size = selected.size * CAMERA_SCALE
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
                file.write(self.get_save_data(self._aux_data))

    def open_file(self, file_path: str):
        self.file_path = file_path
        with open(self.file_path, "rt") as file:
            raw_data = file.read()
            self._aux_data = self.apply_save_data(raw_data)

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
            player.position = Point(x, y) * (1 / CAMERA_SCALE) - player.size * 0.5
            play_world.add_actor(player)
            play_world.add_actor(TestPlayController(editor_world=self.world))

        self.universe.queue_task(switch_world)

    def update(self, delta: float):
        for event in self._input.events:
            self._text_input.update(event, self._input.keys)

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
                elif event.key == pygame.K_DOWN:
                    if self._selected_actor_type is None:
                        continue
                    index = self._search_results.index(self._selected_actor_type)
                    if index + 1 < len(self._search_results):
                        self._selected_actor_type = self._search_results[index + 1]
                elif event.key == pygame.K_UP:
                    if self._selected_actor_type is None:
                        continue
                    index = self._search_results.index(self._selected_actor_type)
                    if index - 1 >= 0:
                        self._selected_actor_type = self._search_results[index - 1]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                mouse_position = Point(x, y)
                if event.button == pygame.BUTTON_RIGHT:
                    if self._selected_actor_type is None:
                        continue
                    # Spawning actor
                    self.push_undo_stack()
                    self.spawn_actor(self._selected_actor_type, mouse_position * (1 / CAMERA_SCALE))
                    self.handle_file_changed()
                elif event.button == pygame.BUTTON_LEFT:
                    for position, size, callback_factory in self.get_selection_handles():
                        if is_intersection(mouse_position, Point.ZERO, position, size):
                            # Clicked on a selection handle, begin its function
                            self.push_undo_stack()
                            self._drag_callback = callback_factory(mouse_position)
                            break
                    else:
                        mouse_world_position = mouse_position * (1 / CAMERA_SCALE)
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

        count = 0
        self._search_results.clear()

        for name, actor_type in ActorRegistry.get_actor_types():
            if count > 5:
                break

            if self._text_input.value.lower() not in name.lower():
                continue

            count += 1
            self._search_results.append(actor_type)

        if self._selected_actor_type not in self._search_results:
            self._selected_actor_type = self._search_results[0] if len(self._search_results) > 0 else None

        if self._selected_actor is not None and self._selected_actor.world is None:
            self._selected_actor = None
