from __future__ import annotations

from typing import TYPE_CHECKING

import requests

from clearskies.di.injectable import Injectable

if TYPE_CHECKING:
    from clearskies.input_outputs.input_output import InputOutput as InputOuputDependency


class InputOutput(Injectable):
    def __init__(self):
        pass

    def __get__(self, instance, parent) -> InputOuputDependency:
        if instance is None:
            return self  # type: ignore
        return self._di.build_from_name("input_output", cache=True)
