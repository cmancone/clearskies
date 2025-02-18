from clearskies.input_outputs import Cli as CliInputOutput
from clearskies.contexts.context import Context


class Cli(Context):
    def __call__(self):
        return self.execute_application(self.di.build(CliInputOutput))
