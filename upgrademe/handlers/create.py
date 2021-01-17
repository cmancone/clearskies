from .base import Base


class Create(Base):
    _request = None
    _models = None
    _authentication = None

    _configuration_defaults = {
        'columns': None,
        'writeable_columns': None,
        'readable_columns': None,
    }

    def __init__(self, request, authentication, models):
        super().__init__(request, authentication)
        self._models = models

    def _check_configuration(self, configuration):
        has_columns = 'columns' in configuration and configuration['columns'] is not None
        has_writeable = 'writeable_columns' in configuration and configuration['writeable_columns'] is not None
        has_readable = 'readable_columns' in configuration and configuration['readable_columns'] is not None
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        if has_columns and has_writeable:
            raise KeyError(f"{error_prefix} you must specify 'columns' OR 'writeable_columns', not both")
        if has_columns and has_readable:
            raise KeyError(f"{error_prefix} you must specify 'columns' OR 'readable_columns', not both")
        if has_writeable and not has_readable:
            raise KeyError(f"{error_prefix} you must specify 'readable_columns' if you specify 'writeable_columns'")
        if has_readable and not has_writeable:
            raise KeyError(f"{error_prefix} you must specify 'writeable_columns' if you specify 'readable_columns'")

        for config_name in ['columns', 'writeable_columns', 'readable_columns']:
            if config_name not in configuration or configuration[config_name] is not None:
                continue
            if type(configuration[config_name]) == list:
                continue
            raise ValueError(
                f"{error_prefix} '{config_name}' should be a list of column names " +
                f", not {str(type(configuration['columns']))}"
            )

    def handle(self):
        pass
