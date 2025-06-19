from clearskies.contexts.context import Context
from clearskies.input_outputs import Cli as CliInputOutput


class Cli(Context):
    def __call__(self):
        return self.execute_application(CliInputOutput())
