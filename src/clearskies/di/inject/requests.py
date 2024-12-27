import requests
from clearskies.di.injectable import Injectable

class Requests(Injectable):
    def __init__(self, cls: type, cache: bool=True):
        if not isinstance(name, type):
            raise TypeError(f"I expected a class for the first argument to clearskies.di.inject.ByClass, but I received an object of type '{name.__class__.__name__}' instead.")
        self.cls = cls
        self.cache = cache

    def __get__(self, instance, parent) -> requests.Session:
        if not instance:
            return self  # type: ignore
        return self._di.build_class(requests.Session, cache=self.cache)
