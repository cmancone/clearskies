from typing import Any
from clearskies.di.injectable import Injectable

class Di(Injectable):
    def __init__(self):
        pass

    def __get__(self, instance, parent) -> Any:
        if not instance:
            return self  # type: ignore
        return self._di
