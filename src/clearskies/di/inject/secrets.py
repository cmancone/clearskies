import datetime
from clearskies.di.injectable import Injectable
from clearskies.secrets import Secrets as SecretsHelper

class Secrets(Injectable):
    def __init__(self, cache: bool=False):
        self.cache = cache

    def __get__(self, instance, parent) -> SecretsHelper:
        if not instance:
            return self  # type: ignore
        return self._di.build_from_name("secrets", cache=self.cache)
