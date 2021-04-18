from .base import Base
from abc import abstractmethod


class Routing(Base):
    def __init__(self, input_output, object_graph):
        super().__init__(input_output, object_graph)

    @abstractmethod
    def handler_classes(self, configuration):
        pass

    @abstractmethod
    def handle(self):
        pass

    def build_handler(self, handler_class, configuration=None):
        if configuration is None:
            configuration = self._configuration
        handler = self._object_graph.provide(handler_class)
        handler_configuration = {}
        for key in handler._configuration_defaults.keys():
            if key in configuration:
                handler_configuration[key] = configuration[key]
        for key in handler._global_configuration_defaults.keys():
            if key in configuration:
                handler_configuration[key] = configuration[key]
        handler.configure(self._finalize_configuration_for_sub_handler(handler_configuration, handler_class))
        return handler

    def _finalize_configuration_for_sub_handler(self, configuration, handler_class):
        return configuration

    def configure(self, configuration):
        # we need to completely clobber the base configuration process because it expects to have
        # the list of all allowed configurations.  We don't know what that list is - rather, we
        # just need to fulfill the requirements of the handlers we'll be routing to.
        # We also want to make it possible for handlers that extend this to still define their
        # own possible configuration values.  Therefore, we'll loop over all of the handlers
        # which we might route to, make them, have them check the configs, and let them throw exceptions
        # as needed.  Finally we'll figure out what configs may not have been "used" by a child handler
        # and see if those are in our own configuration - if not, we'll throw an "Unknown config" exception

        # First, let's check the configuration for the handlers, which is just a matter of building
        # the handlers (they willl automatically throw exceptions for invalid configurations as part
        # of this process)
        used_configs = []
        for handler_class in self.handler_classes(configuration):
            handler = self.build_handler(handler_class, configuration=configuration)
            used_configs.extend(handler._configuration_defaults.keys())

        for key in configuration.keys():
            if key not in used_configs and key not in self._global_configuration_defaults:
                class_name = self.__class__.__name__
                raise KeyError(f"Attempt to set unkown configuration setting '{key}' for handler '{class_name}'")

        self._check_configuration(configuration)
        self._configuration = self._finalize_configuration(self.apply_default_configuation(configuration))

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
