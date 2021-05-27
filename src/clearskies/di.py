from .binding_config import BindingConfig
import inspect


class DI:
    _bindings = None
    _prepared = None
    _building = None

    def __init__(self, classes=None, modules=None, bindings=None):
        self._bindings = {}
        self._prepared = {}
        self._building = {}
        if classes is not None:
            self.add_classes(classes)
        if modules is not None:
            self.add_modules(modules)
        if bindings is not None:
            for (key, value) in bindings.items():
                self.bind(key, value)

    def bind(self, key, value):
        if key in self._buildling:
            raise KeyError(f"Attempt to set binding for '{key}' while '{key}' was already being built")
        self._bindings[key] = value
        if key in self._prepared:
            self._prepared = value

    def build(self, thing):
        if inspect.isclass(thing):
            return self._build_class(thing)
        elif isinstance(thing, BindingConfig):
            instance = self._build_class(thing.object_class)
            if (thing.args or thing.kwargs) and not hasattr(instance, 'configure'):
                raise ValueError(
                    f"Cannot build instance of class '{binding.object_class.__name__}' " + \
                    "because it is missing the 'configure' method"
                )
            instance.configure(*thing.args, **thing.kwargs)
            return instance
        elif type(thing) == str:
            if thing not in self._bindings:
                raise ValueError(f"Requested a build of '{thing}' but this is not a known binding")
            return self.build(self._bindings[thing])
        elif callable(thing):
            return self._execute_method(thing)

        # if we got here then our thing is already instantiated and we can just return it.
        # This seems strange, but it actually just fills in some edge cases
        return thing

    def _build_class(self, class_to_build):
        pass

    def _execute_method(self, callable_to_execute):
        pass
