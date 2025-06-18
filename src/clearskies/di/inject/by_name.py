from typing import Any

from clearskies.di.injectable import Injectable


class ByName(Injectable):
    def __init__(self, name: str, cache: bool = True):
        if not isinstance(name, str):
            raise TypeError(
                f"I expected a string for the first argument to clearskies.di.inject.ByName, but I received an object of type '{name.__class__.__name__}' instead."
            )
        self.name = name
        self.cache = cache

    def __get__(self, instance, parent) -> Any:
        if instance is None:
            return self  # type: ignore
        return self._di.build_from_name(self.name, cache=self.cache)
