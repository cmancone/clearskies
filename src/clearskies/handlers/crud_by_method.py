from .base import Base
from .create import Create
from .update import Update
from .delete import Delete
from .read import Read


class CRUDByMethod(Base):
    _models = None
    _columns = None

    def __init__(self, input_output, authentication, models):
        super().__init__(input_output, authentication)
        self._models = models

    def handle(self):
        pass

    def configure(self, configuration):
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
