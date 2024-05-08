from .. import binding_config
from .api_backend import ApiBackend
from .backend import Backend
from .cursor_backend import CursorBackend
from .example_backend import ExampleBackend
from .file_backend import FileBackend
from .json_backend import JsonBackend
from .memory_backend import MemoryBackend
from .restful_api_advanced_search_backend import RestfulApiAdvancedSearchBackend
from .secrets_backend import SecretsBackend


def example_backend(data):
    return binding_config.BindingConfig(ExampleBackend, data=data)


__all__ = [
    "ApiBackend",
    "Backend",
    "CursorBackend",
    "ExampleBackend",
    "example_backend",
    "FileBackend",
    "JsonBackend",
    "MemoryBackend",
    "RestfulApiAdvancedSearchBackend",
    "SecretsBackend",
]
