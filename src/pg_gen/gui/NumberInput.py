from dataclasses import dataclass
from typing import Callable, override

from ..support.constants import HIGHLIGHT_2_COLOR, TEXT_COLOR
from .TextInput import TextInput


@dataclass
class NumberInput(TextInput):
    integer: bool = False
    on_number_changed: Callable[[float], None] | None = None
    _number_value: float = 0

    @property
    def number_value(self):
        return self._number_value

    @number_value.setter
    def number_value(self, value: float):
        self._number_value = value
        self.color = TEXT_COLOR
        if self.integer:
            self.value = str(int(value))
        else:
            self.value = str(value)

    @override
    def _handle_changed(self):
        value = self.value
        self.color = TEXT_COLOR
        try:
            if self.integer:
                if "." in value:
                    raise ValueError()

                result = int(value)
            else:
                result = float(value)
        except ValueError:
            self.color = HIGHLIGHT_2_COLOR
        else:
            self._number_value = result
            if self.on_number_changed is not None:
                self.on_number_changed(result)

        return super()._handle_changed()
