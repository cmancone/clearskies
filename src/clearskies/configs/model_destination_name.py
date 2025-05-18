from clearskies.configs.string import String
from clearskies.functional import string


class ModelDestinationName(String):
    def __init__(self, model_column_config_name, required=False, default=None):
        self.required = required
        self.default = default
        self.model_column_config_name = model_column_config_name

    def get_model_class(self, instance):
        if self.model_column_config_name:
            return getattr(instance, self.model_column_config_name)
        return None

    def finalize_and_validate_configuration(self, instance):
        # we use the model class itself to decide on our value.  However,
        # if we don't have it yet, don't worry.  Someone will eventually tell us
        # what we need to know
        model_class = self.get_model_class(instance)
        if not model_class:
            return

        instance._set_config(self, model_class.destination_name())
        super().finalize_and_validate_configuration(instance)
