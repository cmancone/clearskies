from __future__ import annotations
from ..binding_config import BindingConfig
import inspect
import re
import sys
import os
from ..functional import string
import logging
from logging import Logger
from typing import Any, Dict, List, Optional, Type, Union
from . import additional_config
class DI:
    _bindings: Dict[str, Any] = {}
    _building: Dict[str, Any] = {}
    _classes: Dict[str, Any] = {}
    _prepared: Dict[str, Any] = {}
    _added_modules: Dict[int, Any] = {}
    _additional_configs: List[additional_config.AdditionalConfig] = []
    log: Optional[Logger] = None
    _di_log: Optional[Logger] = None

    def __init__(
        self,
        classes: Optional[List[Type]] = None,
        modules: Optional[Any] = None,
        bindings: Optional[Dict[str, Any]] = None,
        additional_configs: Optional[List[additional_config.AdditionalConfig]] = None
    ):
        """
        Initializes the dependency injection container.

        Args:
            classes: A list of classes that the DI container should make available for injection.
            modules: A list of modules.  The DI container will recursively search each module
                for classes to make available for injection.
            bindings: A dictionary for the DI container to make available for injection.  The key
                of each dictionary entry will be the injection name.  The value will be the thing to
                inject and can be pre-built values or classes for the DI container to build.
            additional_configs: A list of clearskies.di.AdditionalConfig objects that with instructions
                for building additional dependencies.
        """
        self._bindings = {}
        self._prepared = {}
        self._classes = {}
        self._building = {}
        self._added_modules = {}
        self._additional_configs = []
        if classes is not None:
            self.add_classes(classes)
        if modules is not None:
            self.add_modules(modules)
        if bindings is not None:
            for (key, value) in bindings.items():
                self.bind(key, value)
        if additional_configs is not None:
            self.add_additional_configs(additional_configs)

        # we're going to interact directly with the logging module so pull it out as soon as we're
        # done initializing.  Note that we may already have it because the binding methods are
        # greedy and will grab it if set - this helps ensure that we don't get stuck with an old
        # logging module if the user sets a different one later
        if self.log is None:
            self.set_logger(self.build('logging'))

    def add_classes(self, classes: Union[List[Type], Type]) -> None:
        """
        Add additional classes that the dependency injection container should provide if requested

        The injection name for each class is determined by converting the class name from TitleCase
        to snake_case.  E.g. a class named `MyFancyClass` would have an injection name of `my_fancy_class`.

        Args:
            classes: A class or list of classes to include in the dependency injection container
        """
        if inspect.isclass(classes):
            classes = [classes]    # type: ignore
        for add_class in classes:
            name = string.camel_case_to_snake_case(add_class.__name__)
            #if name in self._classes:
            ## if we're re-adding the same class twice then just ignore it.
            #if id(add_class) == self._classes[name]['id']:
            #continue

            ## otherwise throw an exception
            #raise ValueError(f"More than one class with a name of '{name}' was added")

            self._classes[name] = {'id': id(add_class), 'class': add_class}

            # if this is a model class then also add a plural version of its name
            # to the DI configuration
            if hasattr(add_class, 'id_column_name'):
                self._classes[string.make_plural(name)] = {'id': id(add_class), 'class': add_class}

    def add_modules(self, modules: List[Any], root: Optional[str] = None, is_root: bool = True):
        """
        Add additional modules that the dependency injection container should include for injection.

        The modules will be searched recursively and any classes will be included for injection via
        :py:meth:`clearskies.di.DI.add_classes`.

        Note that this will exclude and core python modules that may have been imported by the given
        module.  This happens by checking the `__file__` attribute on any sub-modules.  If the `__file__`
        attribute does not exist (or has no value), then it is ignored.

        Finally, it tries to also ignore nay third party libraries imported by the module.  When called
        with `is_root=True`, it remembers the directory that the module is located in.  It then checks
        the directory where any sub-modules live in.  If they are not in the same directory as the original
        module, then they are ignored.

        Args:
            modules: A module or list of modules to search/include for injection
            root: The root directory to search - any submodules not in this directory will be ignored
            is_root: If true, the directory of the passed in module will be used as the root directory for the search.
        """
        if inspect.ismodule(modules):
            modules = [modules]

        for module in modules:
            if not hasattr(module, '__file__') or not module.__file__:
                continue
            module_id = id(module)
            if is_root:
                root = os.path.dirname(module.__file__)
            root_len = len(root)    # type: ignore
            if module_id in self._added_modules:
                continue
            self._added_modules[module_id] = True

            for (name, item) in module.__dict__.items():
                if inspect.isclass(item):
                    try:
                        class_root = os.path.dirname(inspect.getfile(item))
                    except TypeError:
                        # built-ins will end up here
                        continue
                    if class_root[:root_len] != root:
                        continue
                    self.add_classes([item])
                if inspect.ismodule(item):
                    if not hasattr(item, '__file__') or not item.__file__:
                        continue
                    child_root = os.path.dirname(module.__file__)
                    if child_root[:root_len] != root:
                        continue
                    if module.__name__ == 'clearskies':
                        break
                    self.add_modules([item], root=root, is_root=False)

    def add_additional_configs(
        self, additional_configs: Union[additional_config.AdditionalConfig, List[additional_config.AdditionalConfig]]
    ):
        """
        Add an AdditionalConfig (or a list of AdditionalConfig) object(s) to the dependency injection container.


        """
        # mypy likes to yell at me for mis-using types when there are two possible types, and doesn't
        # recognize the fact that I'm using type checks to disambiguate these issues.  Therefore, lots
        # of type ignores here.
        if type(additional_configs) != list:
            additional_configs = [additional_configs]    # type: ignore
        for additional_config in additional_configs:    # type: ignore
            self._additional_configs.append(
                additional_config() if inspect.isclass(additional_config) else additional_config    # type: ignore
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
            if key == 'logging':
                self.set_logging(value)
            self._prepared[key] = value

    def build(self, thing, context=None, cache=False):
        if inspect.isclass(thing):
            return self.build_class(thing, context=context, cache=cache)
        elif isinstance(thing, BindingConfig):
            if not inspect.isclass(thing.object_class):
                raise ValueError("BindingConfig contained a non-class!")
            instance = self.build_class(thing.object_class, context=context, cache=cache)
            if (thing.args or thing.kwargs) and not hasattr(instance, 'configure'):
                raise ValueError(
                    f"Cannot build instance of class '{binding.object_class.__name__}' " + \
                    "because it is missing the 'configure' method"
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
        """
        context_note = f" for '{context}'" if context else ''
        log_message = f"Requested to build '{name}'{context_note}: "
        if name == 'di':
            self.di_log(log_message + 'I will return myself')
            return self

        if name in self._prepared and cache:
            self.di_log(log_message + 'I will return it from the cache')
            return self._prepared[name]

        if name in self._bindings:
            self.di_log(log_message + 'I found a binding with a matching name - I will build that')
            built_value = self.build(self._bindings[name], context=context)
            if cache:
                self._prepared[name] = built_value
            return built_value

        if name in self._classes:
            self.di_log(log_message + 'I found a class with a matching name - I will build that')
            built_value = self.build_class(self._classes[name]['class'], context=context)
            if cache:
                self._prepared[name] = built_value
            return built_value

        # additional configs are meant to override ones that come before, with most recent ones
        # taking precedence.  Therefore, start at the end (e.g. FILO instead of FIFO, except nothing actually leaves)
        for index in range(len(self._additional_configs) - 1, -1, -1):
            additional_config = self._additional_configs[index]
            if not additional_config.can_build(name):
                continue
            self.di_log(
                log_message +
                f'I have an additional config named {additional_config.__class__.__name__} that says it can build this, so I will let it do it'
            )
            built_value = additional_config.build(name, self, context=context)
            if cache:
                self._prepared[name] = built_value
            return built_value

        if hasattr(self, f'provide_{name}'):
            self.di_log(
                log_message + 'I have a "provide" function of my own that can build it, so I will call my own function'
            )
            built_value = self.call_function(getattr(self, f'provide_{name}'))
            if cache:
                self._prepared[name] = built_value
            return built_value

        raise ValueError(
            f"I was asked to build {name}{context_note} but there is no added class, configured binding, " + \
            f"or a corresponding 'provide_{name}' method for this name."
        )

    def build_class(self, class_to_build, context=None, name=None, cache=False):
        """
        Builds a class

        The class constructor cannot accept any kwargs.   See self._disallow_kwargs for more details
        """
        if name is None:
            name = string.camel_case_to_snake_case(class_to_build.__name__)
        if name in self._prepared and cache:
            return self._prepared[name]

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
            original_context_label = f"'{self._building[class_id]}'" \
                if self._building[class_id] \
                is not None \
                else 'itself'
            raise ValueError(
                f"Circular dependencies detected while building '{class_to_build.__name__}' because '" + \
                f"{class_to_build.__name__} is a dependency of both '{context}' and {original_context_label}"
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
        if hasattr(callable_to_execute, '__self__'):
            call_arguments = call_arguments[1:]

        args = [
            kwargs[call_argument] if call_argument in kwargs else
            self.build_from_name(call_argument, context=callable_to_execute.__name__, cache=True)
            for call_argument in call_arguments
        ]

        return callable_to_execute(*args)

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

    def set_logger(self, log):
        self.log = log
        self._di_log = logging.getLogger(self.log.name + '.di')

        # log our DI information.
        self._di_log.info('Available dependency injection names in order of increasing priority')
        self._di_log.info('In other words - things on the bottom of this list trump things on top')

        for attribute in dir(self):
            if attribute[:8] != 'provide_':
                continue
            key = attribute[8:]
            self._di_log.info(
                f"Injection name '{key}' provided by dependency injection object of class '{self.__class__.__name__}'"
            )

        for additional_config in self._additional_configs:
            for attribute in dir(additional_config):
                if attribute[:8] != 'provide_':
                    continue
                key = attribute[8:]
                self._di_log.info(f"Injection name '{key}' provided by additional config '{additional_config}'")

        for (key, class_info) in self._classes:
            class_name = class_info['class'].__name__
            self._di_log.info(f"Injection name '{key}' provides class '{class_name}' via class/module binding")

        for (key, value) in self._bindings.items():
            self._di_log.info(f"Injection name '{key}' provides '{value}' via bindings")

        for (key, value) in self._prepared.items():
            self._di_log.info(f"Injection name '{key}' provides '{value}' via bindings")

        self._di_log.info(f"Injection name 'di' provides the dependency injection container")

    def di_log(self, message):
        if not self._di_log:
            return
        self._di_log.debug(message)

    @classmethod
    def init(cls, *binding_classes, **bindings):
        modules = None
        additional_configs = None
        if 'modules' in bindings:
            modules = bindings['modules']
            del bindings['modules']
        if 'additional_configs' in bindings:
            additional_configs = bindings['additional_configs']
            del bindings['additional_configs']

        di = cls(classes=binding_classes, modules=modules, bindings=bindings, additional_configs=additional_configs)
        return di
