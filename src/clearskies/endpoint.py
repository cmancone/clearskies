from __future__ import annotations
from typing import TYPE_CHECKING

import clearskies.configurable

if TYPE_CHECKING:
    from clearskies import Model

class Endpoint(clearskies.configurable.Configurable, clearskies.di.InjectableProperties):
    pass
