import types
import datetime
import uuid

from clearskies.di.injectable import Injectable

class Uuid(Injectable):
    def __init__(self, cache: bool=False):
        self.cache = cache

    def __get__(self, instance, parent) -> uuid:
        if instance is None:
            return self  # type: ignore
        return self._di.build_from_name("uuid", cache=self.cache) # type: ignore
