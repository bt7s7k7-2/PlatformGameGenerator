from dataclasses import dataclass, field
from random import Random
from typing import TYPE_CHECKING, Any, Literal, override

from ..game_core.Camera import CameraClient
from ..game_core.ResourceClient import ResourceClient
from ..generation.RoomInfo import NO_KEY, NOT_CONNECTED
from ..generation.RoomParameter import RoomParameter
from ..generation.RoomPrefabRegistry import RoomPrefabRegistry
from ..level_editor.ActorRegistry import ActorRegistry, ActorType
from ..support.Color import Color
from ..support.constants import TEXT_BG_COLOR, TEXT_COLOR
from ..support.Direction import Direction
from ..support.Point import Point
from ..world.Actor import Actor
from .Placeholders import Placeholder
from .support.ConfigurableObject import ConfigurableObject
from .support.PersistentObject import PersistentObject

if TYPE_CHECKING:
    from ..generation.RoomInstantiationContext import RoomInstantiationContext


SocketCommandResult = ActorType | str | Literal[False]
SocketState = SocketCommandResult | None


@dataclass
class _SocketCommand:
    def get_value(self) -> SocketCommandResult: ...

    def evaluate(self, random: Random, context: "RoomInstantiationContext") -> SocketCommandResult:
        return self.get_value()


@dataclass
class _ActorCommand(_SocketCommand):
    actor: ActorType

    @override
    def get_value(self) -> SocketCommandResult:
        return self.actor


@dataclass
class _RoomCommand(_SocketCommand):
    room_name: str

    @override
    def get_value(self) -> SocketCommandResult:
        return self.room_name


@dataclass
class _ChanceCommand(_SocketCommand):
    chance: float
    target: _SocketCommand
    fallback: _SocketCommand | None

    @override
    def evaluate(self, random: Random, context: "RoomInstantiationContext") -> SocketCommandResult:
        if random.random() < self.chance:
            return self.target.evaluate(random, context)
        elif self.fallback is not None:
            return self.fallback.evaluate(random, context)
        else:
            return False

    @override
    def get_value(self) -> ActorType | str | Literal[False]:
        return self.target.get_value()


_ParameterComparison = Literal[None, "<", "=", ">"]


@dataclass
class _ParameterCommand(_SocketCommand):
    parameter: Direction | RoomParameter
    comparison: _ParameterComparison
    threshold: float
    target: _SocketCommand
    fallback: _SocketCommand | None

    @override
    def evaluate(self, random: Random, context: "RoomInstantiationContext") -> SocketCommandResult:
        parameter: float

        if isinstance(self.parameter, Direction):
            parameter = context.get_connection(self.parameter)
        elif isinstance(self.parameter, RoomParameter):
            parameter = context.get_parameter(self.parameter)

        passes = False
        if self.comparison is None:
            passes = random.random() < parameter
        elif self.comparison == "<":
            passes = parameter < self.threshold
        elif self.comparison == "=":
            passes = parameter == self.threshold
        else:
            passes = parameter > self.threshold

        if passes:
            return self.target.evaluate(random, context)
        elif self.fallback is not None:
            return self.fallback.evaluate(random, context)
        else:
            return False

    @override
    def get_value(self) -> ActorType | str | Literal[False]:
        return self.target.get_value()


@dataclass(kw_only=True)
class Socket(PersistentObject[SocketState], ResourceClient, CameraClient, ConfigurableObject, Placeholder):
    _actor_instance: Actor | None = field(default=None, init=False)

    @property
    def size_string(self):
        return f"{self.size.x}x{self.size.y}"

    def _get_default_persistent_value(self) -> Any:
        return None

    @override
    def apply_config(self, config: str) -> bool:
        super().apply_config(config)

        if self.parse_config() is None:
            return False

        return True

    def parse_config(self):
        arguments = self.config.split(",")
        stack: list[_SocketCommand] = []

        if len(arguments) < 1:
            return None

        for argument in arguments:
            if argument.startswith("@") and len(argument) > 1:
                stack.append(_RoomCommand(argument[1:]))
                continue

            if argument.endswith("%"):
                use_fallback = False
                if argument.startswith("?"):
                    use_fallback = True
                    argument = argument[1:]

                try:
                    chance = int(argument[0:-1]) / 100
                except ValueError:
                    return None

                if not use_fallback:
                    if len(stack) < 1:
                        return None
                    stack.append(_ChanceCommand(chance, stack.pop(), None))
                else:
                    if len(stack) < 2:
                        return None
                    fallback = stack.pop()
                    target = stack.pop()
                    stack.append(_ChanceCommand(chance, target, fallback))

                continue

            if argument.startswith("$") or argument.startswith("?"):
                use_fallback = argument.startswith("?")
                argument = argument[1:]

                comparison_index = next((i for i, c in enumerate(argument) if c in ["<", "=", ">"]), None)
                comparison: _ParameterComparison = None
                threshold_string = None
                if comparison_index is not None:
                    comparison = argument[comparison_index]  # type: ignore
                    threshold_string = argument[comparison_index + 1 :]
                    argument = argument[0:comparison_index]

                threshold = 0.0
                if threshold_string is not None:
                    if threshold_string == "NC":
                        threshold = NOT_CONNECTED
                    elif threshold_string == "NK":
                        threshold = NO_KEY
                    else:
                        try:
                            threshold = float(threshold_string)
                        except ValueError:
                            return None

                parameter_name = argument.upper()
                if parameter_name in Direction._member_map_:
                    parameter = Direction[parameter_name]
                elif parameter_name in RoomParameter._member_map_:
                    parameter = RoomParameter[parameter_name]
                else:
                    return None

                if not use_fallback:
                    if len(stack) < 1:
                        return None
                    stack.append(_ParameterCommand(parameter, comparison, threshold, stack.pop(), None))
                else:
                    if len(stack) < 2:
                        return None
                    fallback = stack.pop()
                    target = stack.pop()
                    stack.append(_ParameterCommand(parameter, comparison, threshold, target, fallback))
                continue

            actor = ActorRegistry.try_find_actor_type(argument)
            if actor is None:
                return None
            stack.append(_ActorCommand(actor))

        if len(stack) != 1:
            return None
        return stack[0]

    @override
    def evaluate_placeholder(self, context: "RoomInstantiationContext"):
        state = self.persistent_value
        assert self.room is not None

        command = self.parse_config()
        if command is None:
            return False

        if state is None:
            state = command.evaluate(Random(self.room.seed + self.flag_index), context)

        self.persistent_value = state

        if isinstance(state, ActorType):
            actor = state.create_instance()
            actor.position = self.position
            actor.size = self.size
            return actor
        elif isinstance(state, str):
            rooms = RoomPrefabRegistry.find_rooms(state, requirements=None, context=context)
            room = Random(context.room.seed + self.flag_index).choice(rooms)

            offset_context = context.create_child(offset=self.position)
            room.instantiate_using(offset_context)
            return False

        return False

    def draw(self):
        self._resource_provider.font.render_to(
            self._camera.screen,
            (self._camera.world_to_screen(self.position) + Point(0, 12)).to_pygame_coordinates(),
            self.size_string,
            fgcolor=TEXT_COLOR,
            bgcolor=TEXT_BG_COLOR,
        )

        result = self.parse_config()

        if result is not None:
            state = result.get_value()
            if isinstance(state, ActorType):
                self._actor_instance = self._actor_instance or state.create_instance()
                self._actor_instance.position = self.position
                self._actor_instance.universe = self.universe
                self._actor_instance.world = self.world
                self._actor_instance.size = self.size
                if hasattr(self._actor_instance, "tint"):
                    self._actor_instance.tint = Color.YELLOW  # type: ignore
                self._actor_instance.draw()
                return super().draw()
            else:
                infill_color = Color.BLACK
                self._camera.draw_placeholder(self.position, self.size, Color.CYAN * 0.75, width=2)
                for y in [0, self.size.y - 1 / self._camera.zoom]:
                    self._camera.draw_placeholder_raw(self._camera.world_to_screen(self.position + Point(0.5, y)), Point(self.size.x - 1, 0) * self._camera.zoom + Point(0, 1), infill_color)
                for x in [0, self.size.x - 1 / self._camera.zoom]:
                    self._camera.draw_placeholder_raw(self._camera.world_to_screen(self.position + Point(x, 0.5)), Point(0, self.size.y - 1) * self._camera.zoom + Point(1, 0), infill_color)

        if self._actor_instance is not None:
            instance = self._actor_instance
            self._actor_instance = None
            self.universe.queue_task(lambda: instance.remove())

        return super().draw()


ActorRegistry.register_actor(Socket)
