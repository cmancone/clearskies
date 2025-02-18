import re

class Headers:
    _headers: dict[str, str] = {}

    def __init__(self, headers: dict[str, str] = {}):
        self.__dict__["headers"] = {*headers} if headers else {}

    def __contains__(self, key: str):
        return key.upper().replace("_", "-") in self._headers

    def __getattr__(self, key: str) -> str | None:
        return self._headers.get(key.upper().replace("_", "-"), None)

    def __setattr__(self, key: str, value: str) -> None:
        if not isinstance(key, str):
            raise TypeError(f"Header keys must be strings, but an object of type '{value.__class__.__name__}' was provided.")
        if not isinstance(value, str):
            raise TypeError(f"Header values must be strings, but an object of type '{value.__class__.__name__}' was provided.")
        self._headers[re.sub("\\s+", " ", key.upper().replace("_", "-"))] = re.sub("\\s+", " ", value)

    def keys(self) -> list[str]:
        return list(self._headers.keys())

    def values(self) -> list[str]:
        return list(self._headers.keys())

    def items(self) -> list[tuple[str]]:
        return list(self._headers.items())

    def add(self, key: str, value: str) -> None:
        """
        Add a header.  This expects a string with a colon separating the key and value
        """
        setattr(self, key, value)
