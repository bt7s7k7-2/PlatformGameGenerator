from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Any, Callable, override

ObjectManifest = list[tuple[str | tuple[str, list, list], type]]


@dataclass()
class AttributeHandle:
    name: str
    type: type
    getter: Callable[[], Any]
    setter: Callable[[Any], Any]

    @staticmethod
    def from_manifest(object: Any, manifest: ObjectManifest):
        result: list[AttributeHandle] = []

        for accessor, type in manifest:
            name = accessor if isinstance(accessor, str) else accessor[0]
            getter = (partial(getattr, object, name)) if isinstance(accessor, str) else partial(accessor[1][0], object, *accessor[1][1:])
            setter = (partial(setattr, object, name)) if isinstance(accessor, str) else partial(accessor[2][0], object, *accessor[2][1:])

            result.append(AttributeHandle(name, type, getter, setter))

        return result


class ObjectManifestParser:
    def handle_string(self, attribute: AttributeHandle):
        self.handle_unknown(attribute)

    def handle_bool(self, attribute: AttributeHandle):
        self.handle_unknown(attribute)

    def handle_list(self, attribute: AttributeHandle):
        self.handle_unknown(attribute)

    def handle_enum(self, enum_values: dict[str, Enum], attribute: AttributeHandle):
        self.handle_unknown(attribute)

    def handle_unknown(self, attribute: AttributeHandle): ...

    def parse(self, manifest: list[AttributeHandle]):
        for attribute in manifest:
            type = attribute.type

            if type is str:
                self.handle_string(attribute)
                continue

            if type is bool:
                self.handle_bool(attribute)
                continue

            if type == list[str]:
                self.handle_list(attribute)
                continue

            if issubclass(type, Enum):
                elements = type._member_map_
                self.handle_enum(elements, attribute)
                continue

            self.handle_unknown(attribute)


class ObjectManifestSerializer[T](ObjectManifestParser):
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}

    @staticmethod
    def serialize(value: Any, manifest: ObjectManifest):
        serializer = ObjectManifestSerializer()
        serializer.parse(AttributeHandle.from_manifest(value, manifest))
        return serializer.result

    @override
    def handle_unknown(self, attribute: AttributeHandle):
        self.result[attribute.name] = attribute.getter()

    @override
    def handle_enum(self, enum_values: dict[str, Enum], attribute: AttributeHandle):
        value: Enum = attribute.getter()
        self.result[attribute.name] = value.name.lower()


class ObjectManifestDeserializer[T](ObjectManifestParser):
    def __init__(self, source: dict[str, Any]) -> None:
        self.source = source

    @staticmethod
    def deserialize[TValue](source: dict[str, Any], value: TValue, manifest: ObjectManifest) -> TValue:
        ObjectManifestDeserializer(source).parse(AttributeHandle.from_manifest(value, manifest))
        return value

    @override
    def handle_unknown(self, attribute: AttributeHandle):
        value = self.source.get(attribute.name, None)

        if value is None:
            if attribute.type is bool:
                attribute.setter(False)
                return

        if type(value) is attribute.type:
            attribute.setter(value)
            return

        raise TypeError(f"Property '{attribute.name}' is not of type '{attribute.type.__name__}'")

    @override
    def handle_list(self, attribute: AttributeHandle):
        value = self.source.get(attribute.name, None)

        if type(value) is list:
            for element in value:
                if type(element) is not str:
                    break
            else:
                attribute.setter(value)
                return

        raise TypeError(f"Property '{attribute.name}' is not of type '{attribute.type.__name__}'")

    @override
    def handle_enum(self, enum_values: dict[str, Enum], attribute: AttributeHandle):
        value = self.source.get(attribute.name, None)

        if value is None:
            attribute.setter(next(iter(enum_values.values())))
            return

        if type(value) is str:
            enum_value = enum_values.get(value.upper(), None)
            if enum_value is not None:
                attribute.setter(enum_value)
                return

        raise TypeError(f"Property '{attribute.name}' is not of type '{attribute.type.__name__}'")
