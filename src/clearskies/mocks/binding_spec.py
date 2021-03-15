from .. import binding_specs
import pinject


class BindingSpec(binding_specs.BindingSpec):
    _bind = None

    def __init__(self, **kwargs):
        self._bind = kwargs

    def provide_requests(self):
        return self._bind['requests'] if 'requests' in self._bind else super().provide_requests()

    def provide_object_graph(self):
        return self._bind['object_graph'] if 'object_graph' in self._bind else super().provide_object_graph()

    def provide_columns(self):
        return self._bind['columns'] if 'requests' in self._bind else super().provide_requests()

    def provide_secrets(self):
        return self._bind['secrets'] if 'secrets' in self._bind else super().provide_secrets()

    def provide_environment(self, secrets):
        return self._bind['environment'] if 'environment' in self._bind else super().provide_environment(secrets)

    def provide_cursor(self, environment):
        return self._bind['cursor'] if 'cursor' in self._bind else super().provide_cursor(environment)

    def provide_now(self):
        return self._bind['now'] if 'now' in self._bind else super().provide_now()

    def provide_input_output(self):
        return self._bind['input_output'] if 'input_output' in self._bind else super().provide_input_output()

    def provide_authentication(self):
        return self._bind['authentication'] if 'authentication' in self._bind else super().provide_authentication()
