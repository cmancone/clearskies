"""
The backend system provides a layer of abstraction between a clearskies model and the place where it stores its data.

## Motivation

The goal of the backend system is to create a standard way to interact with external systems, whether those are
databases, APIs, cloud resources, etc...  For comparison, models in other frameworks typically interact exclusively
with SQL databases.  Therefore, building integrations with other data stores or 3rd party systems requires the
creation of bespoke SDKs, which results in time spent integrating and learning how to use them.  Clearskies models
work with different backends to normalize the process of integrating with data stores and external systems.
This ability to switch backends turns the models, in essence, into a standardized SDK.  The details of how to
interact with some other system are abstracted away into the backend, and then developers can interact with the
system using models in the standard way.

Of course, no abstraction layer is perfect, and not all datastores can fit into the backend system provided by
clearskies.  That's okay!  Like every abstraction layer in clearskies, you should use it when it works for
you and forget about it otherwise.  So, for instance, it is not possible to build arbitrarily complex SQL
queries with the query system provided by models, but you can always inject the cursor and use it directly.
If some arbitrary data store just works in a completely different way, such that the backend system doesn't
work for it, it's still fine to build an SDK the "old school" way and use it in a clearskies application.

## Backends

There are four primary kinds of backends built into clearskies, with a few sub-types.  Those are:

 1. CursorBackend: Store data in an SQL-like database
 2. MemoryBackend: Store data in-memory
 3. ApiBackend: Use an API to fetch and store data
    1. ApiGetOnlyBackend: Only supports fetching individual records from the API by id.
    2. RestfulApiAdvancedSearchBackend: Automatically integrates with APIs built using clearskies.endpoints.RestfulApi
 4. SecretsBackend - Store data directly in a secrets manager

See the documentation for each backend to understand how to configure and use it.  In all cases though, you specify
the backend by instantiating the backend and attaching it to the model class via the `backend` attribute:

```python
import clearskies


class MyModel(clearskies.model):
    backend = clearskies.backends.MemoryBackend()
```
"""

# from .api_backend import ApiBackend
# from .api_get_only_backend import ApiGetOnlyBackend
from clearskies.backends.api_backend import ApiBackend
from clearskies.backends.backend import Backend
from clearskies.backends.cursor_backend import CursorBackend
from clearskies.backends.memory_backend import MemoryBackend

# from .memory_backend import MemoryBackend
# from .restful_api_advanced_search_backend import RestfulApiAdvancedSearchBackend
# from .secrets_backend import SecretsBackend


__all__ = [
    "ApiBackend",
    # "ApiGetOnlyBackend",
    "Backend",
    "CursorBackend",
    "MemoryBackend",
    # "RestfulApiAdvancedSearchBackend",
    # "SecretsBackend",
]
