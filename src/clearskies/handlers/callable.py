from .base import Base
import inspect
import json


class Callable(Base):
    _object_graph = None
    _global_configuration_defaults = {
        'authentication': None,
        'callable': None,
    }

    def __init__(self, object_graph):
        super().__init__(object_graph)

    def handle(self, input_output):
        # Do I regret this?  Yes.  Would I do it again? Probably.
        # In short, pinject only supports dependency injection at object instantiation, and that
        # doesn't work for what we want to do - injection into the arguments of a callable.  Therefore,
        # hacking is required.
        my_callable = self.configuration('callable')
        context = self._object_graph._injection_context_factory.new(my_callable)
        (args, kwargs) = self._object_graph._obj_provider.get_injection_pargs_kwargs(
            my_callable,
            context,
            [],
            {}
        )
        kwargs['input_output'] = input_output

        ordered_args = []
        for name in inspect.getfullargspec(my_callable)[0]:
            ordered_args.append(kwargs[name])
        response = my_callable(*ordered_args)
        if response is not None:
            if type(response) == dict or type(response) == list:
                return input_output.success(json.dumps(response))
            return input_output.success(response)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        if not 'callable' in configuration:
            raise KeyError(f"{error_prefix} you must specify 'callable'")
        if not callable(configuration['callable']):
            raise ValueError(f"{error_prefix} the provided callable is not actually callable")
