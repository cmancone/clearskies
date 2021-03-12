import os.path


class Environment:
    """
    This loads up the environment configuration for the application.

    It looks in 3 possible places: first, it looks in os.environ.  Next, it tries to load up the .env file.
    Therefore, the application root directory should be passed in, at will look for a .env file there.
    It should contain lines like NAME=value.  Finally, if there is a value of `secret://path/to/secret`,
    it will use the secret service to look up the secret value.

    It is a very basic parser.  Empty lines and lines starting with a # will be ignored.  Otherwise everything
    is assumed to be a string.
    """
    _env_file_config = None
    _resolved_values = None

    def __init__(self, env_file_path, os_environ, secrets):
        self._env_file_path = env_file_path
        self.os_environ = os_environ
        self.secrets = secrets
        self._resolved_values = {}

    def get(self, name):
        self._load_env_file()
        if name in self.os_environ:
            return self.resolve_value(self.os_environ[name])
        if name in self._env_file_config:
            return self.resolve_value(self._env_file_config[name])

        raise ValueError(f"Could not find environment config '{name}' in environment or .env file")

    def _load_env_file(self):
        if self._env_file_config is not None:
            return

        self._env_file_config = {}
        if not os.path.isfile(self._env_file_path):
            return

        with open(self._env_file_path, 'r') as env_file:
            line_number = 0
            for line in env_file.readlines():
                line_number += 1
                (key, value) = self._parse_env_line(line, line_number)
                if key is None:
                    continue

                self._env_file_config[key] = value

    def _parse_env_line(self, line, line_number):
        line = line.strip()
        if not line:
            return (None, None)
        if line[0] == '#':
            return (None, None)
        if not '=' in line:
            raise ValueError(f"Parse error in environment line #{line_number}: should be 'key=value'")

        equal_index = line.index('=')
        return (line[:equal_index].strip(), line[equal_index+1:].strip())

    def resolve_value(self, value):
        if value[:9] != 'secret://':
            return value

        secret_path = value[9:]
        if secret_path[0] != '/':
            secret_path = f'/{secret_path}'
        if secret_path not in self._resolved_values:
            if self.secrets is None:
                raise ValueError(
                    "References to the secret engine were found in the environment, " + \
                    "but a secret engine was not provided"
                )
            self._resolved_values[secret_path] = self.secrets.get(secret_path)
        return self._resolved_values[secret_path]
