from clearskies.configs import String
from clearskies.functional import string

class ModelDestinationName(String):
    def finalize_and_validate_configuration(self, instance):

        # we use the model class itself to decide on our value.  However,
        # if we don't have it yet, don't worry.  Someone will eventually tell us
        # what we need to know
        model_class = self.get_model_class()
        if not model_class:
            return
        instance._set_config(self, model_class.destination_name())

        super().finalize_and_validate_configuration(instance)
