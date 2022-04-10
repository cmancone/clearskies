from .base import Base
from io import StringIO
import sys
class Capturing:
    def __init__(self, sys):
        self.sys = sys
        self.output = []

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.output.extend(self._stringio.getvalue().splitlines())
        del self._stringio
        sys.stdout = self._stdout
class Mygrations(Base):
    _connection = None
    _sys = None

    _configuration_defaults = {
        'command': None,
        'allow_input': False,
        'sql': None,
    }

    def __init__(self, di, connection_no_autocommit, sys):
        super().__init__(di)
        self._connection = connection_no_autocommit
        self._sys = sys

    def handle(self, input_output):
        from mygrations.core.commands import execute, commands
        command = self._from_input_or_config('command', input_output)
        if not command:
            return self.error(
                input_output,
                "Must provide 'command' in handler configuration, or in user input after setting the allow_input flag in the handler configuration",
                400
            )
        sql = self._from_input_or_config('sql', input_output)
        if not sql:
            return self.error(
                input_output,
                "Must provide 'sql' in handler configuration, or in user input after setting the allow_input flag in the handler configuration",
                400
            )

        if command not in commands:
            return self.error(
                input_output,
                'Invalid mygrations command.  See allowed list: https://github.com/cmancone/mygrations#command-line-usage',
                400
            )

        [output, success] = execute(command, {'connection': self._connection, 'sql_files': sql}, print_results=False)
        if success:
            return self.success(input_output, output)
        else:
            return self.error(input_output, "\n".join(output), 400)

    def _from_input_or_config(self, key, input_output):
        if self.configuration('allow_input'):
            input_data = input_output.json_body(required=False)
            if input_data is not None and key in input_data:
                return input_data[key]
        return self.configuration(key)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        try:
            import mygrations
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                'You must install mygrations to use the mygrations handler.  See https://github.com/cmancone/mygrations#installation'
            )
