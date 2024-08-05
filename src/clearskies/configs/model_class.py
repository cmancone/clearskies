from clearskies.functional import validations
from . import config

class ModelClass(config.Config):
    """
    A config that accepts a model class.

    Sadly, this one isn't strongly typed because there's just no good way to do so
    that won't cause circular imports.  The model class relies on configs, so we can't
    have a config that relies on the model class.  Have to make do with run-time checks.
    """

    def __set__(self, instance, value):
        if not validations.is_model_class(value):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' when a model class was expected"
            )
        instance._set_config(self, value)

    def __get__(self, instance, parent):
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
