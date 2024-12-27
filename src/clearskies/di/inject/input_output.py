import requests
from clearskies.di.injectable import Injectable
from clearskies.input_outputs.input_output import InputOutput as InputOuputDependency

class InputOutput(Injectable):
    def __init__(self):
        pass

    def __get__(self, instance, parent) -> InputOuputDependency:
        if not instance:
            return self  # type: ignore
        return self._di.build_from_name("input_output", cache=True)
