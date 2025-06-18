import requests

from clearskies.di.injectable import Injectable
from clearskies.environment import Environment as EnvironmentDependency


class Environment(Injectable):
    def __init__(self, cache: bool = True):
        self.cache = cache

    def __get__(self, instance, parent) -> EnvironmentDependency:
        if instance is None:
            return self  # type: ignore
        return self._di.build_from_name("environment", cache=self.cache)
