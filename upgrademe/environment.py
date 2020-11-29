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

    def __init__(self, root_directory, os_environ, secrets):
        self.root_directory = root_directory
        self.os_environ = os_environ
        self.secrets = secrets

    def get(self, name):
        if name in self.os_environ:
            return self.os_environ[name]

        self._load_env_file()
        return self._get_from_env_file(name)

    def _load_env_file(self):
        if self._env_file_config is not None:
            return

        self.env_file_config = {}
        with open(f'{self.root_directory}/.env', 'r') as env_file:
            for line in env_file.readlines():
                (key, value) = self._parse_env_line(line)
                if key is None:
                    continue

                self.env_file_config[key] = value

    def _parse_env_line(line):
        line = line.strip()
        if not line:
            return (None, None)
        if not '=' in line:
            return (None, None)
        if line[0] == '#':
            return (None,,None)

        equal_index = line.index('=')
        return (line[:equal_index].strip(), line[equal_index+1:].strip())

    def _get_from_env_file(self, name):
        if name not in self._env_file_config:
            raise KeyError(f"Requested environment variable '{name}' was not found in .env file")

        value = self._env_file_config[name]
        if value[:9] == 'secret://':
            return self.secrets.get(value[9:])
        return value
