import json
from os import path, walk

from ..support.Direction import Direction
from ..support.ObjectManifest import ObjectManifestDeserializer
from .RoomInfo import NO_KEY, NOT_CONNECTED, RoomInfo
from .RoomPrefab import RoomPrefab, RoomPrefabEntrance


class RoomPrefabRegistry:
    @classmethod
    def find_rooms(cls, group: str, requirements: RoomInfo | None, debug_info: list[str] | None = None):
        result: list[RoomPrefab] = []
        group_rooms = cls.rooms_by_group[group]

        for room in group_rooms:
            if requirements is None:
                result.append(room)
                continue

            if debug_info is not None:
                debug_info.append(f"  Testing room {room.name}")
            if requirements.provides_key != NO_KEY and not room.key:
                if debug_info is not None:
                    debug_info.append(f"    Rejected: need key")
                continue

            rejected = False
            for direction in Direction.get_directions():
                required = requirements.get_connection(direction)
                curr = room.get_connection(direction)
                if required == NOT_CONNECTED:
                    if curr == RoomPrefabEntrance.DOOR or curr == RoomPrefabEntrance.OPEN:
                        rejected = True
                        if debug_info is not None:
                            debug_info.append(f"    Rejected: {direction} need {required} -> {curr}")
                        break
                elif required == NO_KEY:
                    if curr == RoomPrefabEntrance.CLOSED:
                        rejected = True
                        if debug_info is not None:
                            debug_info.append(f"    Rejected: {direction} need {required} -> {curr}")
                        break
                else:
                    if curr != RoomPrefabEntrance.DOOR and curr != RoomPrefabEntrance.ANY:
                        rejected = True
                        if debug_info is not None:
                            debug_info.append(f"    Rejected: {direction} need {required} -> {curr}")
                        break

            if rejected:
                continue
            result.append(room)

        return result

    @classmethod
    def load(cls, room_folder: str):
        cls.rooms_by_group.clear()
        cls.rooms_by_name.clear()

        for directory, _, files in walk(room_folder, onerror=print):
            for room_path in files:
                if not room_path.endswith(".json"):
                    continue

                name = room_path[0:-5]
                room_path = path.join(directory, room_path)
                print(f"Loading room {room_path}...")

                file_content = ""
                with open(room_path, "rt") as file:
                    file_content = file.read()

                raw_data: dict = json.loads(file_content)
                room = RoomPrefab(name, file_content)
                cls.rooms_by_name[name] = room
                config = raw_data["$config"]

                ObjectManifestDeserializer.deserialize(config, room, RoomPrefab.get_manifest())

                for group in room.groups:
                    cls.rooms_by_group.setdefault(group, []).append(room)

                print(f"Loaded room {room}")

                if room.allow_flip:
                    flipped = room.flip()
                    cls.rooms_by_name[flipped.name] = flipped
                    for group in flipped.groups:
                        cls.rooms_by_group.setdefault(group, []).append(flipped)
                    print(f"Loaded room {flipped}")

    rooms_by_name: dict[str, RoomPrefab] = {}
    rooms_by_group: dict[str, list[RoomPrefab]] = {}
