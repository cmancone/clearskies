class Config:
    def __init__(self, required=False, default=None):
        self.required = required
        self.default = default

    def _error_prefix(self, instance) -> str:
        name = instance._descriptor_to_name(self)
        class_name = instance.__class__.__name__
        return f"Error with '{class_name}.{name}':"

    def finalize_and_validate_configuration(self, instance):
        if self.default:
            try:
                instance._get_config(self)
            except KeyError:
                instance._set_config(self.default)

        if self.required and instance._get_config(self) is None:
            name = instance._descriptor_to_name(self)
            prefix = self._error_prefix(instance)
            raise ValueError("{prefix} {name} is a required configuration setting, but no value was set")
