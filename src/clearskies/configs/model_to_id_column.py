from clearskies.configs import model_column
from clearskies.functional import string


class ModelToIdColumn(model_column.ModelColumn):
    def __init__(
        self,
        model_column_config_name="",
        source_model_class=None,
        source_model_class_config_name="",
        required=False,
        default=None,
    ):
        self.required = required
        self.default = default
        self.model_column_config_name = model_column_config_name
        self.source_model_class_config_name = source_model_class_config_name
        self.model_class = None
        self.source_model_class = source_model_class

    def finalize_and_validate_configuration(self, instance):
        # we use the model class itself to decide on our value.  However,
        # if we don't have it yet, don't worry.  Someone will eventually tell us
        # what we need to know
        model_class = self.get_model_class(instance)
        if not model_class:
            return
        if self.source_model_class:
            model_class = self.source_model_class
        elif self.source_model_class_config_name:
            model_class = getattr(instance, self.source_model_class_config_name)

        has_config = False
        try:
            if instance._get_config(self):
                has_config = True
        except KeyError:
            pass

        if not has_config:
            instance._set_config(self, string.camel_case_to_snake_case(model_class.__name__) + "_id")

        super().finalize_and_validate_configuration(instance)
