import importlib
import importlib.resources
from dataclasses import dataclass
from functools import cache
from importlib.abc import Traversable
from typing import Callable


@dataclass
class Assets:
    rooms: Traversable
    actors: Traversable
    spritesheet: Traversable
    font: Traversable


@cache
def get_pg_assets():
    # resources = importlib.resources.files(__name__.split(".")[0])
    resources = importlib.resources.files(__package__)

    return Assets(
        rooms=resources.joinpath("assets/rooms"),
        actors=resources.joinpath("actors"),
        spritesheet=resources.joinpath("assets/spritesheet.png"),
        font=resources.joinpath("assets/Micro5/Micro5-Regular.ttf"),
    )


def walk_files_recursive(directory: Traversable, callback: Callable[[Traversable, str], None]):
    def load_directory(dir: Traversable, path: str):
        for entry in dir.iterdir():
            if entry.name == "__pycache__":
                continue

            if entry.is_dir():
                load_directory(entry, path + "." + entry.name)
            elif entry.is_file():
                callback(entry, path + "." + entry.name)

    load_directory(directory, "")
