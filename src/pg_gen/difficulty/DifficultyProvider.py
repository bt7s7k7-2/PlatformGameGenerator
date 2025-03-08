

from .DifficultyReport import DifficultyReport


class DifficultyProvider:
    def apply_difficulty(self, difficulty: DifficultyReport): ...

