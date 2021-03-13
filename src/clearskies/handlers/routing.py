from .base import Base
from abc import abstractmethod


class Routing(Base):
    def __init__(self, input_output, authentication):
        super().__init__(input_output, authentication)

    @abstractmethod
    def handler_classes(self):
        pass

    def handle(self):
        pass

    def build_handler(self, handler_class, configuration=None):
        if configuration is None:
            configuration = self._configuration
        handler = handler_class()
        handler_configuration = {}
        for key in handler._configuration_defaults.keys():
            if key in configuration:
                handler_configuration[key] = configuration[key]
        for key in handler._global_configuration_defaults.keys():
            if key in configuration:
                handler_configuration[key] = configuration[key]
        handler.configure(handler_configuration)
        return handler

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
        for handler_class in self.handler_classes():
            handler = self.build_handler(handler_class)

        for key in configuration.keys():
            if key not in self._configuration_defaults and key not in self._global_configuration_defaults:
                class_name = self.__class__.__name__
                raise KeyError(f"Attempt to set unkown configuration setting '{key}' for handler '{class_name}'")

        self._check_configuration(configuration)
        self._configuration = self._finalize_configuration(self.apply_default_configuation(configuration))

    def _check_configuration(self, configuration):
        # we check configuration by passing our configuration on to Create and Read, since those two
        # together will check all necessary configuration.  This is mildly tricky though because they have
        # different configs, and will complain if we pass them something they aren't expecting.
        # However, we can look at their configuration defaults to see what keys they are expecting,
        # and only pass those (if present)
        # also, keep track of the configs they are expecting and make sure we don't have any extras
        for handler_class in [Create, Read]:
            handler = handler_class(self._input_output, self._authentication, self._models)
            handler_config = {}
            for key in handler._configuration_defaults.keys():
                if key in configuration:
                    handler_config[key] = configuration[key]
            for key in handler._global_configuration_defaults.keys():
                if key in configuration:
                    handler_config[key] = configuration[key]
            handler.configure(configuration)
