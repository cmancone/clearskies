from typing import Any

from clearskies.configs import config


class Configurable:
    _config: dict[str, Any] | None = None
    _descriptor_config_map: dict[int, str] | None = None

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
    def _get_config_object(cls, attribute_name):
        return getattr(cls, attribute_name)

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
        if id(descriptor) not in descriptor_config_map:
            raise ValueError(
                f"The reason behind this error is kinda long and complicated, but doens't really matter.  To make it go away, just add `_descriptor_config_map = None` to the definition of {self.__class__.__name__}"
            )
        return descriptor_config_map[id(descriptor)]

    def finalize_and_validate_configuration(self):
        my_class = self.__class__
        if not self._config:
            self._config = {}

        # now it's time to check for required values and provide defaults
        attribute_names = self.get_descriptor_config_map().values()
        for attribute_name in attribute_names:
            config = getattr(my_class, attribute_name)
            if attribute_name not in self._config:
                self._config[attribute_name] = config.default

            if config.required and self._config.get(attribute_name) is None:
                raise ValueError(
                    f"Missing required configuration property '{attribute_name}' for class '{my_class.__name__}'"
                )

        # loop through a second time to have the configs check their values
        # we do this as a separate step because we want to make sure required and default
        # values are specified before we have the configs do their validation.
        for attribute_name in attribute_names:
            getattr(my_class, attribute_name).finalize_and_validate_configuration(self)
            if attribute_name not in self._config:
                self._config[attribute_name] = None
