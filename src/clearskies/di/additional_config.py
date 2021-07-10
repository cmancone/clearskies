class AdditionalConfig:
    _config = None

    def __init__(self, config=None):
        self.config = config if config else {}

    def can_build(self, name):
        return hasattr(self, f'provide_{name}')

    def build(self, name, di, context=None):
        if not hasattr(self, f'provide_{name}'):
            raise KeyError(
                f"AdditionalConfig class '{self.__class__.__name__}' cannot build requested dependency, '{name}'"
            )

        return di.call_function(getattr(self, f'provide_{name}'))
