import datetime

from clearskies.di.injectable import Injectable


class Utcnow(Injectable):
    def __init__(self, cache: bool = False):
        self.cache = cache

    def __get__(self, instance, parent) -> datetime.datetime:
        if instance is None:
            return self  # type: ignore
        return self._di.build_from_name("utcnow", cache=self.cache)
