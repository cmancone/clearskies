import requests

from clearskies.di.injectable import Injectable


class Requests(Injectable):
    def __init__(self, cache: bool = True):
        self.cache = cache

    def __get__(self, instance, parent) -> requests.Session:
        if instance is None:
            return self  # type: ignore
        return self._di.build_from_name("requests", cache=self.cache)
