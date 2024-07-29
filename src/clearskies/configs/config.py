class Config:
    def __init__(self, required=False, default=None):
        self.required = required
        self.default = default

    def _error_prefix(self, instance) -> str:
        name = instance._descriptor_to_name(self)
        class_name = instance.__class__.__name__
        return f"Error with '{class_name}.{name}': "
