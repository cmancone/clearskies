from __future__ import annotations
from ..binding_config import BindingConfig
import inspect
import re
import sys
import os
from ..functional import string
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union
from . import additional_config

log = logging.getLogger(__name__)

class DI:
    _bindings: Dict[str, Any] = {}
    _building: Dict[int, Any] = {}
    _classes: Dict[str, Any] = {}
    _prepared: Dict[str, Any] = {}
    _added_modules: Dict[int, Any] = {}
    _additional_configs: List[additional_config.AdditionalConfig] = []
    _class_mocks: Dict[str, Any] = {}

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
        self._class_mocks = {}
        if classes is not None:
            self.add_classes(classes, debug=False)
        if modules is not None:
            self.add_modules(modules, debug=False)
        if bindings is not None:
            for (key, value) in bindings.items():
                self.bind(key, value, debug=False)
        if additional_configs is not None:
            self.add_additional_configs(additional_configs, debug=False)

        self.dump_debug_info()

    def add_classes(self, classes: Union[List[Type], Type], debug: bool = True) -> None:
        """
        Add additional classes that the dependency injection container should provide if requested

        The injection name for each class is determined by converting the class name from TitleCase
        to snake_case.  E.g. a class named `MyFancyClass` would have an injection name of `my_fancy_class`.

        Note that while this can be called on the dependency injection container directly, it is primarily
        exposed via the `binding_classes` kwarg in the constructor, which is also exposed when creating contexts.

        Per DI norms, the DI container will provide any arguments declared in the constructor of the class.
        However, it will raise an exception if the constructor requests any kwargs.  For reasons why,
        as well as instructions on how to override this behavior, see the `_disallow_kwargs` method in this class.

        Example:
            The following example uses the `binding_classes` kwarg on the context constructor to add a class as dependency.
            The DI name for the class is automatically determined by converting the class name to snake case.

                import clearskies
                class MyAwesomeService():
                    def __init__(self, now):
                        self.now = now
                    def fetch_a_cool_thing(self):
                        return self.now.year
                def my_function(my_awesome_service):
                    print(my_awesome_service.fetch_a_cool_thing())
                cli = clearskies.contexts.cli(
                    my_function,
                    binding_classes=[MyAwesomeService],
                )
                cli()

        Args:
            classes: A class or list of classes to include in the dependency injection container
            debug: If true, add a debug entry about the newly set class
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

            class_name = add_class.__name__
            self._classes[name] = {'id': id(add_class), 'class': add_class}

            if debug:
                log.info("Injection name '{name}' provides class '{class_name}' via class/module binding")

            # if this is a model class then also add a plural version of its name
            # to the DI configuration
            if hasattr(add_class, 'id_column_name'):
                plural_name = string.make_plural(name)
                self._classes[plural_name] = {'id': id(add_class), 'class': add_class}
                if debug:
                    log.info("Injection name '{plural_name}' provides class '{class_name}' via class/module binding")


    def add_modules(self, modules: List[Any], root: Optional[str] = None, is_root: bool = True, debug: bool = True):
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
            debug: If true, a line will be added to the debugger for each class found and added.
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
                    self.add_classes([item], debug=debug)
                if inspect.ismodule(item):
                    if not hasattr(item, '__file__') or not item.__file__:
                        continue
                    child_root = os.path.dirname(item.__file__)
                    if child_root[:root_len] != root:
                        continue
                    if module.__name__ == 'clearskies':
                        break
                    self.add_modules([item], root=root, is_root=False, debug=debug)

    def add_additional_configs(
        self, additional_configs: Union[additional_config.AdditionalConfig, List[additional_config.AdditionalConfig]], debug: bool = True
    ):
        """
        Add an AdditionalConfig (or a list of AdditionalConfig) object(s) to the dependency injection container.

        AdditionalConfig objects take precedence over any "standard" dependencies

        Note that while this can be called on the dependency injection container directly, it is primarily
        exposed via the `additional_configs` kwarg in the constructor, which is also exposed when creating contexts.

        Example:
            The following example uses the additional_configs kwarg on the context constructor, which is passed into
            to the constructor of the dependency injection container.

                import datetime
                import clearskies
                class DateTimeOverride(clearskies.di.AdditionalConfig):
                    def provide_now(self):
                        import datetime
                        return datetime.datetime.now() - datetime.timedelta(weeks=520)
                def my_function(now):
                    print(now.year)

                # default behavior without our additional config
                cli = clearskies.contexts.cli(
                    my_function,
                )
                cli()
                # prints:
                # 2023

                # with the additional config
                cli = clearskies.contexts.cli(
                    my_function,
                    additional_configs=[DateTimeOverride],
                )
                cli()
                # prints:
                # 2013

`       Args:
            additional_configs: An instance of the clearskies.di.AdditionalConfig class, or a list of such instances
            debug: If true, a line will be added to the debugger for each "provide_" function in the additional configs.
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
            for attribute in dir(additional_config):
                if attribute[:8] != 'provide_':
                    continue
                key = attribute[8:]
                log.info(f"Injection name '{key}' provided by additional config '{additional_config}'")

    def bind(self, key: str, value: Any, debug: bool = True):
        """
        Binds a given value to a dependency injection name

        The value can be either a pre-built value (string, int, float, instance, etc...), a class, or a.
        clearskies.BindingConfig object.  Classes/binding configs will not be instantiated until some
        actually requests them, at which point in time they will have their own dependencies provided
        via the usual dependency injection process.

        Note that while this can be called on the dependency injection container directly, it is primarily
        exposed via the `bindings` kwarg in the constructor, which is also exposed when creating contexts.

        Example:
            The following example uses the bindings kwarg on the context constructor, which is passed into
            to the constructor of the dependency injection container, and then through this bind method.

                import clearskies
                def my_function(my_first_dependency, my_second_dependency):
                    print(my_first_dependency + ' ' + my_second_dependency)
                cli = clearskies.contexts.cli(
                    my_function,
                    bindings={
                        'my_first_dependency': 'this is a',
                        'my_second_dependency': 'simple example',
                    },
                )
                cli()
                # prints
                # this is a simple example

        Args:
            key: The dependency injection name to make the value available at
            value: The value to provide
            debuug: If true, a line will be added to the debug log for each binding added.
        """
        if key in self._building:
            raise KeyError(f"Attempt to set binding for '{key}' while '{key}' was already being built")

        # classes and binding configs are placed in self._bindings, but any other prepared value goes straight
        # into self._prepared
        if inspect.isclass(value) or isinstance(value, BindingConfig):
            self._bindings[key] = value
            if key in self._prepared:
                del self._prepared[key]
            if inspect.isclass(value):
                log.info(f"Injection name '{key}' provided by direct binding with class {value.__name__}")
            else:
                log.info(f"Injection name '{key}' provided by direct binding of BindingConfig with class {value.object_class.__name__}")
        else:
            self._prepared[key] = value
            log.info(f"Injection name '{key}' provided by direct binding with value {value}")


    def build(self, thing: Any, context: Optional[str] = None, cache: bool = False) -> Any:
        """
        Builds the dependency given by `thing`

        The thing to build can be a dependency injection name, a class, or a clearskies.BindingConfig object.
        In order of priority, thing will be interpreted as follows:

            1. If a class, it will be built.  Arguments in the constructors will be provided by the DI container.
            2. If a BindingConfig instance, it will be built and configured per BindingConfig norms.
            3. If a string, it will be interpreted as a dependency injection name and the corresponding value will be returned.
            4. If it is a callable, it will be called and any parameters will be provided by the DI container.
            5. Otherwise, thing itself will be returned

        Note: returning `thing` itself as the fallback behavior helps the DI container with processing bindings

        Args:
            thing: The thing to build.  See notes above to understand allowed value
            context: A string that represents what the value is being built for.
            cache: Whether or not to fetch/store from the DI cache.  If False, a new instance will be built

        Returns:
            The corresponding, built value
        """
        if inspect.isclass(thing):
            return self.build_class(thing, context=context, cache=cache)
        elif isinstance(thing, BindingConfig):
            if not inspect.isclass(thing.object_class):
                raise ValueError("BindingConfig contained a non-class!")
            instance = self.build_class(thing.object_class, context=context, cache=cache)
            if (thing.args or thing.kwargs) and not hasattr(instance, 'configure'):
                raise ValueError(
                    f"Cannot build instance of class '{thing.object_class.__name__}' " + \
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

    def can_build(self, name: str) -> bool:
        """
        Returns True/False to denote if the DI container can build the dependency with the given name

        Note: This only checks the requested dependency - it doesn't check for sub-depenencies.

        Args:
            name: The dependency name to check

        Returns:
            Whether or not the dependency can be built
        """
        if name == 'di':
            return True
        if name in self._prepared:
            return True
        if name in self._bindings:
            return True
        if name in self._classes:
            return True
        for additional_config in self._additional_configs:
            if additional_config.can_build(name):
                return True
        if hasattr(self, f'provide_{name}'):
            return True
        return False

    def build_from_name(self, name: str, context: Optional[str] = None, cache: bool = False) -> Any:
        """
        Builds a dependency based on its name

        Order of priority:
          1. 'di': return this dependency injection container
          2. Already prepared things
          3. Things set via `bind(name, value)`
          4. Class via add_classes or add_modules
          5. Things set in "additional_config" classes
          6. Method on DI class called `provide_[name]`

        Args:
            thing: The thing to build.  See notes above to understand allowed value
            context: A string that represents what the value is being built for.
            cache: Whether or not to fetch/store from the DI cache.  If False, a new instance will be built

        Returns:
            The built value
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

    def mock_class(self, class_or_name: Any, replacement: Any) -> None:
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
                + type(replacement)
            )

        self._class_mocks[name] = replacement

    def build_class(
        self,
        class_to_build: type,
        context: Optional[str] = None,
        name: Optional[str] = None,
        cache: bool = False
    ) -> Any:
        """
        Builds a class

        Note on names: Names only matter when cache=True.  The name determines what dependency injection name the class uses
        in the cache.  By default, the class name is converted to snake case and that is used as the dependency injeciton name.

        Note that the class constructor cannot accept any kwargs.   See self._disallow_kwargs for more details, including
        how to override this behavior

        Args:
            class_to_build: The class that you want the DI container to build.
            context: A string that represents what the value is being built for.
            name: The key in the cache to fetch/store the built instance in
            cache: Whether or not to fetch/store from the DI cache.  If False, a new instance will be built

        Returns:
            An instance of the class
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

    def call_function(self, callable_to_execute: Callable, **kwargs: Dict[str, Any]) -> Any:
        """
        Calls a function, building any positional arguments and providing them.

        Any kwargs passed to `call_function` will populate the equivalent args and kwargs in the function
        to be called, overriding any arguments that might otherwise be provided by the DI container.
        You can also provide kwargs for the function in this way.  If the function has args that cannot
        be provided by the DI container and which are not provided to `call_function` via a kwarg,
        then an error will be raised.  If the function has a kwarg which cannot be provided by the DI
        container and which is not provided to `call_function` via a kwarg, then the kwarg will simply
        not be provided when calling the function.

        Note:
            This will not raise an error if you provide a kwarg that the function does not accept

        Example:
            The following example uses the `call_function` method to call a function, provides some values
            for the functions args/kwargs, and lets the DI container provide the rest.

                import clearskies
                import datetime
                def add_time(now, delta=None):
                    if delta:
                        return (now + delta).year
                    return now.year
                def my_function(di):
                    print(di.call_function(add_time))
                    print(di.call_function(add_time, now=datetime.datetime(year=2024, month=1, day=1)))
                    print(di.call_function(add_time, delta=datetime.timedelta(weeks=104)))
                cli = clearskies.contexts.cli(my_function)
                cli()
                # prints:
                # 2023
                # 2024
                # 2025

        Args:
            callable_to_execute: A callable to execute
            kwargs: Any additional key/value pairs to provide to the calling function

        Returns:
            The return value of the function that was executed
        """
        args_data = inspect.getfullargspec(callable_to_execute)

        # We're going to treat args and kwargs a bit differently, so we have to separate them
        total_number_callable_args = len(args_data.args)
        number_callable_kwargs = len(args_data.defaults) if args_data.defaults else 0
        arg_separator_index = total_number_callable_args - number_callable_kwargs
        call_args = args_data.args[:arg_separator_index]
        call_kwargs = args_data.args[arg_separator_index:]
        # we need to decide if we've been passed a bound method, because then we need to ignore the
        # first argument (aka `self`/`cls`).  The simplest way to do this is to see if the first argument
        # is named 'self' or 'cls'.  Note that these names are set by convention - not by python - so
        # it may fail in some cases: https://stackoverflow.com/a/50074581/1921979
        if call_args and call_args[0] in ['cls', 'self']:
            call_args = call_args[1:]

        # now build the args.  Note that the end-user is allowed to override both args and kwargs
        # for the call, which come in via the kwargs param on this call.  This is why we're populating
        # args from the kwargs - it makes passing things through a bit easier.
        final_args = [
            kwargs[call_arg]
            if call_arg in kwargs else self.build_from_name(call_arg, context=callable_to_execute.__name__, cache=True)
            for call_arg in call_args
        ]

        # remember that we want to ignore any kwargs that we can't provide.
        final_kwargs = {}
        for call_kwarg in call_kwargs:
            if call_kwarg in kwargs:
                final_kwargs[call_kwarg] = kwargs[call_kwarg]
            elif self.can_build(call_kwarg):
                self.build_from_name(call_kwarg, context=callable_to_execute.__name__, cache=True)

        return callable_to_execute(*final_args, **final_kwargs)

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

    def dump_debug_info(self):
        """ Dumps all the debug data into the logger. """
        # log our DI information.
        log.info('Available dependency injection names in order of increasing priority')
        log.info('In other words - things on the bottom of this list trump things on top')

        for attribute in dir(self):
            if attribute[:8] != 'provide_':
                continue
            key = attribute[8:]
            log.info(
                f"Injection name '{key}' provided by dependency injection object of class '{self.__class__.__name__}'"
            )

        for additional_config in self._additional_configs:
            for attribute in dir(additional_config):
                if attribute[:8] != 'provide_':
                    continue
                key = attribute[8:]
                log.info(f"Injection name '{key}' provided by additional config '{additional_config}'")

        for (key, class_info) in self._classes.items():
            class_name = class_info['class'].__name__
            log.info(f"Injection name '{key}' provides class '{class_name}' via class/module binding")

        for (key, value) in self._bindings.items():
            log.info(f"Injection name '{key}' provides '{value}' via bindings")

        for (key, value) in self._prepared.items():
            log.info(f"Injection name '{key}' provides '{value}' via bindings")

        log.info("Injection name 'di' provides the dependency injection container")
        log.info("This concludes the list of dependencies added at at the moment,")
        log.info("*BUT* more can still be added later, so check below for the full record or call di.dump_debug_info() again.")

    @classmethod
    def init(cls: type, *binding_classes: List[Any], **bindings: Dict[str, Any]) -> Any:
        """
        Initializes a dependency injection class so that it can be used for binding.

        To be honest, I don't remember why I created this instead of just using the constructor.

        Example:
            Initialize a dependency injection container!

                import clearskies
                di = clearskies.StandardDependencies.init(
                    SomeClass,
                    SomeOtherClass,
                    bindings={'some': 'binding'},
                    modules=[SomeModule],
                    additional_configs=[AdditionalConfig],
                )
                print(di.build('now').year)
        """
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
