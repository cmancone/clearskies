from clearskies.configs import string


class ReadableModelColumns(string.String):
    def finalize_and_validate_configuration(self, instance):
        super().finalize_and_validate_configuration(instance)
