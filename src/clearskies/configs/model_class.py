from __future__ import annotations
import inspect

import clearskies.model
from clearskies.functional import validations
from clearskies.configs import config


class ModelClass(config.Config):
    """
    A config that accepts a model class.

    Sadly, this one isn't strongly typed because there's just no good way to do so
    that won't cause circular imports.  The model class relies on configs, so we can't
    have a config that relies on the model class.  We have to make do with run-time checks.
    """

    def __set__(self, instance, value: type[clearskies.model.Model]):
        try:
            validations.is_model_class_or_reference(value, raise_error_message=True)
        except TypeError as e:
            error_prefix = self._error_prefix(instance)
            raise TypeError(f"{error_prefix} {str(e)}")

        # reference or model class?
        if validations.is_model_class_reference(value):
            if inspect.isclass(value):
                value = value()
            instance._set_config(self, value.get_model_class())  # type: ignore
        else:
            instance._set_config(self, value)

    def __get__(self, instance, parent) -> type[clearskies.model.Model]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
