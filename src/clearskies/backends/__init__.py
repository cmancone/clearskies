"""
Flexible data storage locations for clearskies models.

The backend system provides a layer of abstraction between a clearskies model and the place where it stores its data.
Rather than tying models to a single data source (for instance, an SQL database), clearskies allows the developers
to choose a backend for each model class.  There are four primary kinds of backends built into clearskies, although
the API backend comes with a few sub-classes to support common use-cases:

 1. CursorBackend: Store data in an SQL-like database
 2. MemoryBackend: Store data in memory
 3. ApiBackend: Use an API to fetch and store data
    1. ApiGetOnlyBackend: Only supports fetching individual records from the API by id.
    2. RestfulApiAdvancedSearchBackend: Automatically integrates with APIs built using clearskies.endpoints.RestfulApi
 4. SecretsBackend - Store data directly in a secrets manager

See the documentation for each backend to understand how to configure and use it.  In all cases though, you specify
the backend by attaching it to the model class via the `backend` attribute:

```
import clearskies

class MyModel(clearskies.model):
    backend = clearskies.backends.MemoryBackend()
```
"""

#from .api_backend import ApiBackend
#from .api_get_only_backend import ApiGetOnlyBackend
from clearskies.backends.backend import Backend
from clearskies.backends.memory_backend import MemoryBackend
#from .cursor_backend import CursorBackend
#from .memory_backend import MemoryBackend
#from .restful_api_advanced_search_backend import RestfulApiAdvancedSearchBackend
#from .secrets_backend import SecretsBackend


__all__ = [
    #"ApiBackend",
    #"ApiGetOnlyBackend",
    "Backend",
    #"CursorBackend",
    "MemoryBackend",
    #"RestfulApiAdvancedSearchBackend",
    #"SecretsBackend",
]
