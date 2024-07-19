from ..binding_config import BindingConfig
from .additional_config_auto_import import AdditionalConfigAutoImport
import inspect
import re
import sys
import os
from ..functional import string


class DI:
    _bindings = None
    _building = None
    _classes = None
    _prepared = None
    _added_modules = None
    _additional_configs = None
    _class_mocks = None

    def __init__(self, classes=None, modules=None, bindings=None, additional_configs=None):
        self._bindings = {}
        self._prepared = {}
        self._classes = {}
        self._building = {}
        self._added_modules = {}
        self._additional_configs = []
        self._class_mocks = {}
        if classes is not None:
            self.add_classes(classes)
        if modules is not None:
            self.add_modules(modules)
        if bindings is not None:
            for key, value in bindings.items():
                self.bind(key, value)
        if additional_configs is not None:
            self.add_additional_configs(additional_configs)

    def add_classes(self, classes):
        if inspect.isclass(classes):
            classes = [classes]
        for add_class in classes:
            name = string.camel_case_to_snake_case(add_class.__name__)
            # if name in self._classes:
            ## if we're re-adding the same class twice then just ignore it.
            # if id(add_class) == self._classes[name]['id']:
            # continue

            ## otherwise throw an exception
            # raise ValueError(f"More than one class with a name of '{name}' was added")

            self._classes[name] = {"id": id(add_class), "class": add_class}

            # if this is a model class then also add a plural version of its name
            # to the DI configuration
            if hasattr(add_class, "id_column_name"):
                self._classes[string.make_plural(name)] = {"id": id(add_class), "class": add_class}

    def add_modules(self, modules, root=None, is_root=True):
        if inspect.ismodule(modules):
            modules = [modules]

        for module in modules:
            if not hasattr(module, "__file__") or not module.__file__:
                continue
            module_id = id(module)
            if is_root:
                root = os.path.dirname(module.__file__)
            root_len = len(root)
            if module_id in self._added_modules:
                continue
            self._added_modules[module_id] = True

            for name, item in module.__dict__.items():
                if inspect.isclass(item):
                    try:
                        class_root = os.path.dirname(inspect.getfile(item))
                    except TypeError:
                        # built-ins will end up here
                        continue
                    if class_root[:root_len] != root:
                        continue
                    if issubclass(item, AdditionalConfigAutoImport):
                        init_args = inspect.getfullargspec(item)
                        nargs = len(init_args.args) if init_args.args else 0
                        nkwargs = len(init_args.defaults) if init_args.defaults else 0
                        if nargs - 1 - nkwargs > 0:
                            raise ValueError(
                                "Error auto-importing additional config "
                                + item.__name__
                                + ": auto imported configs can only have keyword arguments."
                            )
                        self.add_additional_configs([item()])
                        continue
                    self.add_classes([item])
                if inspect.ismodule(item):
                    if not hasattr(item, "__file__") or not item.__file__:
                        continue
                    child_root = os.path.dirname(item.__file__)
                    if child_root[:root_len] != root:
                        continue
                    if module.__name__ == "clearskies":
                        break
                    self.add_modules([item], root=root, is_root=False)

    def add_additional_configs(self, additional_configs):
        if type(additional_configs) != list:
            additional_configs = [additional_configs]
        for additional_config in additional_configs:
            self._additional_configs.append(
                additional_config() if inspect.isclass(additional_config) else additional_config
            )

    def bind(self, key, value):
        if key in self._building:
            raise KeyError(f"Attempt to set binding for '{key}' while '{key}' was already being built")

        # classes and binding configs are placed in self._bindings, but any other prepared value goes straight
        # into self._prepared
        if inspect.isclass(value) or isinstance(value, BindingConfig):
            self._bindings[key] = value
            if key in self._prepared:
                del self._prepared[key]
        else:
            self._prepared[key] = value

    def build(self, thing, context=None, cache=False):
        if inspect.isclass(thing):
            return self.build_class(thing, context=context, cache=cache)
        elif isinstance(thing, BindingConfig):
            if not inspect.isclass(thing.object_class):
                raise ValueError("BindingConfig contained a non-class!")
            instance = self.build_class(thing.object_class, context=context, cache=cache)
            if (thing.args or thing.kwargs) and not hasattr(instance, "configure"):
                raise ValueError(
                    f"Cannot build instance of class '{instance.__class__.__name__}' "
                    + "because it is missing the 'configure' method"
                )
            instance.configure(*thing.args, **thing.kwargs)
            return instance
        elif type(thing) == str:
            return self.build_from_name(thing, context=context, cache=cache)
        elif callable(thing):
            raise ValueError("build received a callable: you probably want to call di.call_function()")

        # if we got here then our thing is already and object of some sort and doesn't need anything further
        return thing

    def build_from_name(self, name, context=None, cache=False):
        """
        Builds a dependency based on its name

        Order of priority:
          1. 'di' (aka self)
          2. Already prepared things
          3. Things set via `bind(name, value)`
          4. Class via add_classes or add_modules
          5. Things set in "additional_config" classes
          6. Method on DI class called `provide_[name]`
          7. Already prepared things
        """
        if name == "di":
            return self

        if name in self._prepared and cache:
            return self._prepared[name]

        if name in self._bindings:
            built_value = self.build(self._bindings[name], context=context)
            if cache:
                self._prepared[name] = built_value
            return built_value

        if name in self._classes:
            built_value = self.build_class(self._classes[name]["class"], context=context)
            if cache:
                self._prepared[name] = built_value
            return built_value

        # additional configs are meant to override ones that come before, with most recent ones
        # taking precedence.  Therefore, start at the end (e.g. FILO instead of FIFO, except nothing actually leaves)
        for index in range(len(self._additional_configs) - 1, -1, -1):
            additional_config = self._additional_configs[index]
            if not additional_config.can_build(name):
                continue
            built_value = additional_config.build(name, self, context=context)
            if cache and self.call_function(additional_config.can_cache, name=name, context=context):
                self._prepared[name] = built_value
            return built_value

        if hasattr(self, f"provide_{name}"):
            built_value = self.call_function(getattr(self, f"provide_{name}"))
            if cache:
                self._prepared[name] = built_value
            return built_value

        # why twice?  When a "concrete" value is bound directly to a DI name, it is just
        # put directly in the cache.  Therefore, if cache=False, we won't find it (which is a bug).
        # Therefore, if we get to the very bottom, haven't found anything, but it is in the
        # cache: well, it's time to use the cache.
        if name in self._prepared:
            return self._prepared[name]

        context_note = f" for {context}" if context else ""
        raise ValueError(
            f"I was asked to build {name}{context_note} but there is no added class, configured binding, "
            + f"or a corresponding 'provide_{name}' method for this name."
        )

    def mock_class(self, class_or_name, replacement):
        if type(class_or_name) == str:
            name = class_or_name
        elif inspect.isclass(class_or_name):
            name = string.camel_case_to_snake_case(class_or_name.__name__)
        else:
            raise ValueError(
                "Invalid value passed to 'mock_class' for 'class_or_name' parameter: it was neither a name nor a class"
            )
        if not inspect.isclass(replacement):
            raise ValueError(
                "Invalid value passed to 'mock_class' for 'replacement' parameter: a class should be passed but I got a "
                + str(type(replacement))
            )

        self._class_mocks[name] = replacement

    def build_class(self, class_to_build, context=None, name=None, cache=False):
        """
        Builds a class

        The class constructor cannot accept any kwargs.   See self._disallow_kwargs for more details
        """
        if name is None:
            name = string.camel_case_to_snake_case(class_to_build.__name__)
        if name in self._prepared and cache:
            return self._prepared[name]

        if name in self._class_mocks:
            class_to_build = self._class_mocks[name]

        init_args = inspect.getfullargspec(class_to_build)
        if init_args.defaults is not None:
            self._disallow_kwargs(f"build class '{class_to_build.__name__}'")

        # ignore the first argument because that is just `self`
        build_arguments = init_args.args[1:]
        if not build_arguments:
            built_value = class_to_build()
            if cache:
                self._prepared[name] = built_value
            return built_value

        # self._building will help us keep track of what we're already building, and what we are building it for.
        # This is partly to give better error messages, but mainly to detect cyclical dependency trees.
        # We use id(class_to_build) because this uniquely identifies a class (while the name won't, since two
        # different classes can have the same name but be in different modules).  Therefore, before we start
        # building a class, see if its id is in self._building, raise an error if so, or continue if not.
        class_id = id(class_to_build)
        if class_id in self._building:
            original_context_label = (
                f"'{self._building[class_id]}'" if self._building[class_id] is not None else "itself"
            )
            raise ValueError(
                f"Circular dependencies detected while building '{class_to_build.__name__}' because '"
                + f"{class_to_build.__name__} is a dependency of both '{context}' and {original_context_label}"
            )

        self._building[class_id] = context
        # Turn on caching when building the automatic dependencies that get injected into a class constructor
        args = [
            self.build_from_name(build_argument, context=class_to_build.__name__, cache=True)
            for build_argument in build_arguments
        ]
        del self._building[class_id]

        built_value = class_to_build(*args)
        if cache:
            self._prepared[name] = built_value
        return built_value

    def call_function(self, callable_to_execute, **kwargs):
        """
        Calls a function, building any positional arguments and providing them.

        Any kwargs passed to call_function will populate the equivalent dependencies
        """
        args_data = inspect.getfullargspec(callable_to_execute)

        # we need to decide if we've been passed a bound method, because then we need to ignore the
        # first argument (aka `self`).  The simplest way to do this is to check for the `__self__` attr,
        # but this will be fooled by methods with decorators.  There doesn't seem to be a good solution to this
        # that works in all cases: https://stackoverflow.com/a/50074581/1921979
        call_arguments = args_data.args
        if hasattr(callable_to_execute, "__self__"):
            call_arguments = call_arguments[1:]

        # separate out args and kwargs.  kwargs for the function are only allowed to come out of the kwargs
        # we were passed.  If the function has a kwarg that we don't have, then ignore it.
        # args come out of dependencies or the kwargs passed to us.  If an arg is missing, then throw an error.
        nargs = len(call_arguments)
        nkwargs = len(args_data.defaults) if args_data.defaults else 0
        arg_names = call_arguments[: nargs - nkwargs]
        kwarg_names = call_arguments[nargs - nkwargs :]

        callable_args = [
            kwargs[arg]
            if arg in kwargs
            else self.build_from_name(arg, context=callable_to_execute.__name__, cache=True)
            for arg in arg_names
        ]
        callable_kwargs = {}
        for kwarg_name in kwarg_names:
            if kwarg_name not in kwargs:
                continue
            callable_kwargs[kwarg_name] = kwargs[kwarg_name]

        return callable_to_execute(*callable_args, **callable_kwargs)

    def _disallow_kwargs(self, action):
        """
        Raises an exception

        This is used to raise an exception and stop building a class if its constructor accepts kwargs. To be clear,
        we actually can support kwargs - it just doesn't make much sense.  The issue is that keywords are
        optional, so a dependency injection framework doesn't know what to do with them.  Ignore them?  Provide them?
        The behavior is unclear, and therefore, bug prone.

        If you need to create a class that accepts kwargs in its constructor you can do  that though - just override
        this method in your DI class and don't raise an exception.  If you do that, everything will still work but
        nothing will be provided for your kwargs.

        Another option would be to do a self.build_from_name on the kwargs names, but only provide the kwarg
        if the name is something that the DI container can actually provide (and otherwise just let it fall back
        on the default).  However, I'm not convinced that will be a helpful use case, so I'm not implementing
        it right now.
        """
        raise ValueError(f"Cannot {action} because it has keyword arguments.")

    @classmethod
    def init(cls, *binding_classes, **bindings):
        modules = None
        additional_configs = None
        if "modules" in bindings:
            modules = bindings["modules"]
            del bindings["modules"]
        if "additional_configs" in bindings:
            additional_configs = bindings["additional_configs"]
            del bindings["additional_configs"]

        di = cls(classes=binding_classes, modules=modules, bindings=bindings, additional_configs=additional_configs)
        return di
