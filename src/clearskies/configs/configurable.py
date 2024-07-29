from typing import Any, Dict, Optional

from . import config


class Configurable:
    _config: Optional[Dict[str, Any]] = None
    _descriptor_config_map: Optional[Dict[int, str]] = None

    def _set_config(self, descriptor, value):
        if not self._config:
            self._config = {}

        self._config[self._descriptor_to_name(descriptor)] = value

    def _get_config(self, descriptor):
        if not self._config:
            self._config = {}

        name = self._descriptor_to_name(descriptor)
        if name not in self._config:
            raise KeyError(f"Attempt to fetch a config value named '{name}' but no value has been set for this config")
        return self._config[name]

    @classmethod
    def get_descriptor_config_map(cls):
        if cls._descriptor_config_map:
            return cls._descriptor_config_map

        descriptor_config_map = {}
        for attribute_name in dir(cls):
            descriptor = getattr(cls, attribute_name)
            if not isinstance(descriptor, config.Config):
                continue

            descriptor_config_map[id(descriptor)] = attribute_name

        cls._descriptor_config_map = descriptor_config_map
        return cls._descriptor_config_map

    def _descriptor_to_name(self, descriptor):
        descriptor_config_map = self.get_descriptor_config_map()
        return descriptor_config_map[id(descriptor)]

    def finalize_and_validate_configuration(self):
        my_class = self.__class__
        for attribute_name in self.get_descriptor_config_map().values():
            config = getattr(my_class, attribute_name)
            if config.default is not None and attribute_name not in self._config:
                self._config[attribute_name] = config.default

            if config.required and not self._config.get(attribute_name):
                raise ValueError(
                    f"Missing required configuration property '{attribute_name}' for class '{my_class.__name__}'"
                )
