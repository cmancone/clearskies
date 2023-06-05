from typing import Any, Optional

class DiShim:
    def build(self, thing: Any, context: Optional[str] = None, cache: bool = False) -> Any:
        raise NotImplementedError()
