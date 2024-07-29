from clearskies.functional import validations
from . import config
from .. import model


class ModelClass(config.Config):
    """
    A config that accepts a model class.
    """

    def __set__(self, instance, value: model.Model):
        if not validations.is_model_class(value):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' when a model class was expected"
            )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> model.Model:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
