from .base import Base


class Create(Base):
    _request = None
    _models = None
    _authentication = None

    _allowed_configs = [
        'writeable_columns',
        'readable_columns'
    ]

    def __init__(self, request, models, authentication):
        self._request = request
        self._models = models
        self._authentication = authentication

    def configure(self, configuration):
        self._check_configuration(configuration)
        self._configuration = configuration

    def handle(self, request):
        self.authenticate(request)

    def _check_configuration(self, configuration):
        for key in configuration.keys():
            if not key in self._allowed_configs:
                raise KeyError(f"'{configuration}' is not an allowed config for the Create handler")
