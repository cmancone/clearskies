from clearskies.configs import model_column
from clearskies.functional import string


class ModelToIdColumn(model_column.ModelColumn):
    def finalize_and_validate_configuration(self, instance):
        # we use the model class itself to decide on our value.  However,
        # if we don't have it yet, don't worry.  Someone will eventually tell us
        # what we need to know
        model_class = self.get_model_class(instance)
        if not model_class:
            return

        if not instance._get_config(self):
            instance._set_config(self, string.camel_case_to_snake_case(model_class.__name__) + "_id")

        super().finalize_and_validate_configuration(instance)
