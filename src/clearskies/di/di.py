import datetime
from typing import Any, Callable
from types import ModuleType
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import inspect
import re
import sys
import os

from clearskies.di.additional_config import AdditionalConfig
from clearskies.di.additional_config_auto_import import AdditionalConfigAutoImport
from clearskies.functional import string
from clearskies.environment import Environment
import clearskies.input_outputs.input_output
import clearskies.secrets


class Di:
    """
    Build a dependency injection object.

    The dependency injection (DI) container is a key part of clearskies, so understanding how to both configure
    them and get dependencies for your classes is important.  Note however that there you don't often have
    to interact with the dependency injection container directly.  All of the configuration options for
    the DI container are also available to all the contexts, which is typically how you will build clearskies
    applications.  So, while you can create a DI container and use it directly, typically you'll just follow
    the same basic techniques to configure your context and use that to run your application.

    These are the main ways to configure the DI container:

     1. Import classes - each imported class is assigned an injection name based on the class name.
     2. Import modules - clearskies will iterate over the module and import all the classes and AdditionalConfigAutoImport classes it finds.
     3. Import AdditionalConfig classes - these allow you to programmatically define dependencies.
     4. Specify bindings - this allows you to provide any kind of value with whatever name you want.
     5. Specify class overrides - these allow you to swap out classes directly.
     6. Extending the Di class - this allows you to provide a default set of values.

    When the DI system builds a class or calls a function, those classes and functions can themselves request any value
    configured inside the DI container.  There are three ways to request the desired dependencies:

     1. By type hinting a class on any arguments (excluding python built-ins)
     2. By specifying the name of a registered dependency
     3. By extending the `clearskies.di.AutoFillProps` class and creating class properties from the `clearskies.di.inject_from` module

    Note that when a class is built/function is called by the DI container, keyword arguments are not allowed
    (because the DI container doesn't know whether or not it should provide optional arguments).  In addition,
    the DI container must be able to resolve all positional arguments.  If the class requests an argument
    that the DI system does not recognize, an error will be thrown.  Finally, it's a common pattern in clearskies
    for some portion of the system to accept functions that will be called by the DI container.  When this happens,
    it's possible for clearskies to provide additional values that may be useful when executing the function.
    The areas that accept functions like this also document the additional dependency injection names that are available.

    Given the variety of ways that dependencies can be specified, it's important to understand the order the priority that
    clearskies uses to determine what value to provide in case there is more than one source.  That order is:

     1. Positional arguments with type hints:
        1. The override class if the type-hinted class has a registered override
        2. A value provided by an AdditionalConfig that can provide the type-hinted class
        3. The class itself if the class has been added explicitly via add_classes or implicitly via add_modules
        4. A clearskies built-in for predefined types
     2. All other positional arguments will have values provided based on the argument name and will receive
        1. Things set via `add_binding(name, value)`
        2. Class added via `add_classes` or `add_modules` which are made available according to their Di name
        3. An AdditionalConfig class with a corresponding `provide_[name]` function
        4. A clearskies built-in for predefined names

    Here is the list of predefined values with their names and types:

    | Injection Name       | Injection Type                                          | Value                                                                                     |
    |----------------------|---------------------------------------------------------|-------------------------------------------------------------------------------------------|
    | di                   | -                                                       | The active Di container                                                                   |
    | now                  | -                                                       | The current time in a datetime object, without timezone                                   |
    | utcnow               | -                                                       | The current time in a datetime object, with timezone set to UTC                           |
    | requests             | requests.Session                                        | A requests object configured to allow a small number of retries                           |
    | input_output         | clearskies.input_outputs.InputOutput                    | The clearskies builtin used for receiving and sending data to the client                  |
    | uuid                 | -                                                       | `import uuid` - the uuid module builtin to python                                         |
    | environment          | clearskies.Environment                                  | A clearskies helper that access config info from the environment or a .env file           |
    | sys                  | -                                                       | `import sys` - the sys module builtin to python                                           |
    | oai3_schema_resolver | -                                                       | Used by the autodoc system                                                                |
    | connection_details   | -                                                       | A dictionary containing credentials that pymysql should use when connecting to a database |
    | connection           | -                                                       | A pymysql connection object                                                               |
    | cursor               | -                                                       | A pymysql cursor object                                                                   |

    Note: for dependencies with an injection name but no injection type, this means that to inject those values you
    must name your argument with the given injection name.  In all of the above cases though you can still add type
    hints if desired.  So, for instance, you can declare an argument of `utcnow: datetime.datetime`.  clearskies
    will ignore the type hint (since `datetime.datetime` isn't a type with a predefined value in clearskies) and
    identify the value based on the name of the argument.

    Note: multiple `AdditionalConfig` classes can be added to the Di container, and so a single injection name or class
    can potentially be provided by multiple AdditionalConfig classes.  AdditionalConfig classes are checked in the
    reverse of the order they were addded in - classes added last are checked first when trying to find values.

    Note: When importing modules, any classes that inherit from `AdditionalConfigAutoImport` are automatically added
    to the list of additional config classes.  These classes are added at the top of the list, so they are lower
    priority than any classes you add via `add_additional_configs` or the `additional_configs` argument of the Di
    constructor.

    Note: Once a value is constructed, it is cached by the Di container and will automatically be provided for future
    references of that same Di name or class.  Arguments injected in a constructor will always receive the cached
    value.  If you want a "fresh" value of a given dependency, you have to attach instances from the
    `clearskies.di.inject` module onto class proprties.  The instances in the `inject` module generally
    give options for cache control.

    Here's an example that brings most of these pieces together.  Once again, note that we're directly using
    the Di contianer to build class/call functions, while normally you configure the Di container via your context
    and then clearskies itself will build your class or call your functions as needed.  Full explanation comes after
    the example.

    ```
    from clearskies.di import Di, AdditionalConfig

    class SomeClass:
        def __init__(self, my_value: int):
            self.my_value = my_value

    class MyClass:
        def __init__(self, some_specific_value: int, some_class: SomeClass):
            # `some_specific_value` is defined in both `MyProvider` and `MyOtherProvider`
            # `some_class` will be injected from the type hint, and the actual instance is made by our
            # `MyProvider`
            self.final_value = some_specific_value*some_class.my_value

    class VeryNeedy:
        def __init__(self, my_class, some_other_value: str):
            # We're relying on the automatic conversion of class names to snake_case, so clearskies
            # will connect `my_class` to `MyClass`, which we provided directly to the Di container.

            # some_other_value is specified as a binding
            self.my_class = my_class
            self.some_other_value = some_other_value

    class MyOtherProvider(AdditionalConfig):
        def provide_some_specific_value(self):
            # the order of additional configs will cause this function to be invoked
            # (and hence some_specific_value will be `10`) despite the fact that MyProvider
            # also has a `provide_` function with the same name.
            return 10

    class MyProvider(AdditionalConfig):
        def provide_some_specific_value(self):
            # note that the name of our function matches the name of the argument
            # expected by MyClass.__init__.  Again though, we won't get called because
            # the order the AdditionalConfigs are loaded gives `MyOtherProvider` priority.
            return 5

        def can_build_class(self, class_to_check: type) -> bool:
            # this lets the DI container know that if someone wants an instance
            # of SomeClass, we can build it.
            return class_to_check == SomeClass

        def build_class(self, class_to_provide: type, argument_name: str, di, context: str = ""):
            if class_to_provide == SomeClass:
                return SomeClass(5)
            raise ValueError(f"I was asked to build a class I didn't expect '{class_to_provide.__name__}'")

    di = Di(
        classes=[MyClass, VeryNeedy, SomeClass],
        additional_configs=[MyProvider(), MyOtherProvider()],
        bindings={
            "some_other_value": "dog",
        },
    )

    def my_function(my_fancy_argument: VeryNeedy):
        print(f"Jane owns {my_fancy_argument.my_class.final_value}:")
        print(f"{my_fancy_argument.some_other_value}s")

    print(di.call_function(my_function))
    # prints 'Jane owns 50 dogs'
    ```

    When `call_function` is executed on `my_function`, the di system checks the calling arguments of `my_function`
    and runs through the priority list above to populate them.  `my_function` has one argument -
    `my_fancy_argument: VeryNeedy`, which it resolves as so:

     1. The type hint (`VeryNeedy`) matches an imported class.  Therefore, clearskies will build an instance of VeryNeedy and
        provide it for `my_fancy_argument`.
     2. clearskies inpsects the constructor for `VeryNeedy` and finds two arguments, `my_class` and `some_other_value: str`,
        which it attempts to build.
        1. `my_class` has no type hint, so clearskies falls back on name-based resolution.  A class called `MyClass` was imported,
           and per standard naming convention, this automatically becomes available via the name `my_class`.  Thus, clearskies
           prepares to build an instance of `MyClass`. `MyClass` has two arguments: `some_specific_value: int` and
           `some_class: SomeClass`
           1. For `some_specific_value`, the Di service falls back on named-based resolution (because it will never try to
              provide values for type-hints of built-in types).  Both `MyOtherProvider` and `MyProvider` have a method called
              `provide_some_specific_value`, so both can be used to provide this value.  Since `MyOtherProvider` was added to
              the Di container last, it takes priority.  Therefore, clearskies calls `MyOtherProvider.provide_some_specific_value`
              to create the value that it will populate into the `some_specific_value` parameter.
           2. For `some_class: SomeClass`, clearskies evaluates the type-hint.  It works through the additional configs and, since
              `MyProvider` returns True when `can_build_class` is called with  `SomeClass`, the Di container will use this
              additional config to create the value for the `some_class` argument.  Therefore, clearskies calls
              `MyProvider.build_class(SomeClass, 'some_class', di)` and the return value is used for the `some_class` argument.
        2. `some_other_value` uses a built-in for a type hint, so clearskies falls back on name-based resolution.  It falls back
           on the registered binding of `"dog"` to the name `"some_other_value"`, so clearskies provides `"dog"`.
    """
    _added_modules: dict[int, bool] = {}
    _additional_configs: list[AdditionalConfig] = []
    _bindings: dict[str, Any] = {}
    _building: dict[int, str] = {}
    _classes: dict[str, dict[str, int | type]] = {}
    _prepared: dict[str, Any] = {}
    _class_overrides_by_name: dict[str, type] = {}
    _class_overrides_by_class: dict[type, type] = {}
    _type_hint_disallow_list = [int, float, str, dict, list, datetime.datetime]
    _now: datetime.datetime | None = None
    _utcnow: datetime.datetime | None = None
    _predefined_classes_name_map: dict[type, str] = {
        requests.Session: "requests",
        clearskies.input_outputs.input_output.InputOutput: "input_output",
        Environment: "environment",
    }

    def __init__(
        self,
        classes: type | list[type]=[],
        modules: ModuleType | list[ModuleType]=[],
        bindings: dict[str, Any]={},
        additional_configs: AdditionalConfig | list[AdditionalConfig]=[],
        class_overrides: dict[type, type]={},
        overrides: dict[str, type]={},
        now: datetime.datetime | None = None,
        utcnow: datetime.datetime | None = None,
    ):
        """
        Create a dependency injection container.

        For details on the parameters, see the related methods:

        classes -> di.add_classes()
        modules -> di.add_modules()
        bindings -> di.add_binding()
        additional_configs -> di.add_additional_configs()
        class_overrides -> di.add_class_override()
        """
        self._added_modules = {}
        self._additional_configs = []
        self._bindings = {}
        self._building = {}
        self._classes = {}
        self._class_overrides_by_name = {}
        self._class_overrides_by_class = {}
        self._prepared = {}
        if classes is not None:
            self.add_classes(classes)
        if modules is not None:
            self.add_modules(modules)
        if bindings is not None:
            for key, value in bindings.items():
                self.add_binding(key, value)
        if additional_configs is not None:
            self.add_additional_configs(additional_configs)
        if class_overrides:
            for (key, value) in class_overrides.items():  # type: ignore
                self.add_class_override(key, value)  # type: ignore
        if overrides:
            for (key, value) in overrides.items():
                self.add_override(key, value)
        if now:
            self.set_now(now)
        if utcnow:
            self.set_utcnow(utcnow)

    def add_classes(self, classes: type | list[type]) -> None:
        """
        Record any class that should be made available for injection.

        All classes that come in here become available via their injection name, which is calculated
        by converting the class name from TitleCase to snake_case.  e.g. the following class:

        ```
        class MyClass:
            pass
        ```

        gets an injection name of `my_class`.  Also, clearskies will only resolve and reject based on type hints
        if those classes are first added via `add_classes`.  See the following example:

        ```
        from clearskies.di import Di

        class MyClass:
            name = "Simple Demo"

        di = Di(classes=[MyClass])
        # equivalent: di.add_classes(MyClass), di.add_classes([MyClass])

        def my_function(my_class):
            print(my_class.name)

        def my_function_with_type_hinting(the_name_no_longer_matters: MyClass):
            print(my-class.name)

        # both print 'Simple Demo'
        di.call_function(my_function)
        di.call_function(my_function_with_type_hinting)
        ```
        """
        if not isinstance(classes, list):
            classes = [classes]
        for add_class in classes:
            name = string.camel_case_to_snake_case(add_class.__name__)
            self._classes[name] = {"id": id(add_class), "class": add_class}
            self._classes[add_class] = {"id": id(add_class), "class": add_class}  # type: ignore

            # if this is a model class then also add a plural version of its name
            # to the DI configuration
            if hasattr(add_class, "id_column_name"):
                self._classes[string.make_plural(name)] = {"id": id(add_class), "class": add_class}

    def add_modules(self, modules: ModuleType | list[ModuleType], root: str | None=None, is_root: bool=True) -> None:
        """
        Add a module to the dependency injection container.

        clearskies will iterate through the module, adding all imported classes into the dependency injection container.

        So, consider the following file structure inside a module:

        ```
        my_module/
            __init__.py
            my_sub_module/
                __init__.py
                my_class.py
        ```

        Assuming that the submodule and class are imported at each level (e.g. my_module/__init__.py imports my_sub_module,
        and my_sub_module/__init__.py imports my_class.py) then you can:

        ```
        from clearksies.di import Di
        import my_module

        di = Di()
        di.add_modules([my_module]) # also equivalent: di.add_modules(my_module), or Di(modules=[my_module])
        def my_function(my_class):
            pass

        di.call_function(my_function)
        ```

        `my_function` will be called and `my_class` will automatically be populated with an instance of
        `my_module.sub_module.my_class.MyClass`.

        Note that MyClass will be able to declare its own dependencies per normal dependency injection rules.
        See the main docblock in the clearskies.di.Di class for more details about how all the pieces work together.
        """
        if not isinstance(modules, list):
            modules = [modules]

        for module in modules:
            # skip internal python modules
            if not hasattr(module, "__file__") or not module.__file__:
                continue
            module_id = id(module)
            if is_root:
                root = os.path.dirname(module.__file__)
            root_len = len(root) if root else 0
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

    def add_additional_configs(self, additional_configs: AdditionalConfig | list[AdditionalConfig]) -> None:
        """
        Adds an additional config instance to the dependency injection container.

        Additional config class provide an additional way to provide dependencies into the dependency
        injection system.  For more details about how to use them, see both base classes:

         1. clearskies.di.additional_config.AdditionalConfig
         2. clearskies.di.additional_config_auto_import.AdditionalConfigAutoImport

        To use this method:

        ```
        import clearskies.di

        class MyConfig(clearskies.di.AdditionalConfig):
            def provide_some_value(self):
                return 2

            def provide_another_value(self, some_value):
                return some_value*2

        di = clearskies.di.Di()
        di.add_additional_configs([MyConfig()])
        # equivalents:
        # di.add_additional_configs(MyConfig())
        # di = clearskies.di.Di(additional_configs=[MyConfig()])

        def my_function(another_value):
            print(another_value) # prints 4

        di.call_function(my_function)
        ```
        """
        if not isinstance(additional_configs, list):
            additional_configs = [additional_configs]
        self._additional_configs.extend(additional_configs)

    def add_binding(self, key, value):
        """
        Provide a specific value for name-based injection.

        This method attaches a value to a specific dependency injection name.

        ```
        import clearskies.di

        di = clearskies.di.Di()
        di.add_binding("my_name", 12345)
        # equivalent:
        # di = clearskies.di.Di(bindings={"my_name": 12345})

        def my_function(my_name):
            print(my_name) # prints 12345

        di.call_function(my_function)
        ```
        """
        if key in self._building:
            raise KeyError(f"Attempt to set binding for '{key}' while '{key}' was already being built")

        # classes are placed in self._bindings, but any other prepared value goes straight into self._prepared
        if inspect.isclass(value):
            self._bindings[key] = value
            if key in self._prepared:
                del self._prepared[key]
        else:
            self._prepared[key] = value

    def add_class_override(self, class_to_override: type, replacement_class: type) -> None:
        """
        Overrides a class for type-based injection.

        This function allows you to replace/mock class provided when relying on type hinting for injection.
        This is most often (but not exclusively) used for mocking out classes during texting.  Note that
        this only overrides that specific class - not classes that extend it.

        Example:

        ```
        from clearskies.import Di

        class TypeHintedClass:
            my_value = 5

        class ReplacementClass:
            my_value = 10

        di = Di()
        di.add_classes(TypeHintedClass)
        di.add_class_override(TypeHintedClass, ReplacementClass)
        # also di = Di(class_overrides={TypeHintedClass: ReplacementClass})

        def my_function(some_value: TypeHintedClass):
            print(some_value.my_value) # prints 10

        di.call_function(my_function)
        ```
        """
        if not inspect.isclass(class_to_override):
            raise ValueError(
                "Invalid value passed to add_class_override for 'class_or_name' parameter: it was neither a name nor a class"
            )
        if not inspect.isclass(replacement_class):
            raise ValueError(
                "Invalid value passed to add_class_override for 'replacement_class' parameter: a class should be passed but I got a "
                + str(type(replacement_class))
            )

        self._class_overrides_by_class[class_to_override] = replacement_class

    def add_override(self, name: str, replacement_class: type) -> None:
        """
        Overrides a specific injection name by specifying a class that should be injected in its place.
        """
        if not inspect.isclass(replacement_class):
            raise ValueError(
                "Invalid value passed to add_override for 'replacement_class' parameter: a class should be passed but I got a "
                + str(type(replacement_class))
            )

        self._class_overrides_by_name[name] = replacement_class

    def set_now(self, now: datetime.datetime) -> None:
        """
        Set the current time which will be passed along to any dependency arguments named `now`.
        """
        if now.tzinfo is not None:
            raise ValueError("set_now() was passed a datetime object with timezone information - it should only be given timezone-naive datetime objects.  Maybe you meant to use di.set_utcnow()")
        self._now = now

    def set_utcnow(self, utcnow: datetime.datetime) -> None:
        """
        Set the current time which will be passed along to any dependency arguments named `utcnow`.
        """
        if not utcnow.tzinfo:
            raise ValueError("set_utcnow() was passed a datetime object without timezone information - it should only be given timezone-aware datetime objects.  Maybe you meant to use di.set_now()")
        self._utcnow = utcnow

    def build(self, thing: Any, context: str | None=None, cache: bool=False) -> Any:
        """
        Have the dependency injection container build a value for you.

        This will accept either a dependency injection name or a class.
        """
        if inspect.isclass(thing):
            return self.build_class(thing, context=context, cache=cache)
        elif type(thing) == str:
            return self.build_from_name(thing, context=context, cache=cache)
        elif callable(thing):
            raise ValueError("build received a callable: you probably want to use di.call_function()")

        # if we got here then our thing is already and object of some sort and doesn't need anything further
        return thing

    def build_from_name(self, name: str, context: str | None=None, cache: bool=False) -> Any:
        """
        Builds a dependency based on its name

        Order of priority:
          1. Things set via `add_binding(name, value)`
          2. Class added via `add_classes` or `add_modules` which are made available according to their Di name
          3. An AdditionalConfig class with a corresponding `provide_[name]` function
          4. The Di class itself if it has a matching `provide_[name]` function (aka the builtins)
        """
        if name in self._prepared and cache:
            return self._prepared[name]

        if name in self._bindings:
            built_value = self.build(self._bindings[name], context=context)
            if cache:
                self._prepared[name] = built_value
            return built_value

        if name in self._classes or name in self._class_overrides_by_name:
            class_to_build = self._class_overrides_by_name[name]["class"] if name in self._class_overrides_by_name else self._classes[name]["class"]  # type: ignore
            built_value = self.build_class(class_to_build, context=context)  # type: ignore
            if cache:
                self._prepared[name] = built_value  # type: ignore
            return built_value

        # additional configs are meant to override ones that come before, with most recent ones
        # taking precedence.  Therefore, start at the end (e.g. FILO instead of FIFO, except nothing actually leaves)
        for index in range(len(self._additional_configs) - 1, -1, -1):
            additional_config = self._additional_configs[index]
            if not additional_config.can_build(name):
                continue
            built_value = additional_config.build(name, self, context if context else "")
            if cache and additional_config.can_cache(name, self, context if context else ""):
                self._prepared[name] = built_value
            return built_value

        if hasattr(self, f"provide_{name}"):
            built_value = self.call_function(getattr(self, f"provide_{name}"))
            if cache and self.can_cache(name, context if context else ""):
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

    def build_argument(self, argument_name: str, type_hint: type | None, context: str="", cache: bool = True) -> Any:
        """
        Build an argument given the name and type hint.

        Runs through the resolution order described in the docblock at the top of the Di class to build an argument given
        its name and type-hint.
        """
        built_value = self.build_class_from_type_hint(argument_name, type_hint, context=context, cache=True)
        if built_value:
            return built_value
        return self.build_from_name(argument_name, context=context, cache=True)

    def build_class(self, class_to_build: type, context=None, cache=True) -> Any:
        """
        Builds a class.

        The class constructor cannot accept any kwargs.   See self._disallow_kwargs for more details
        """
        if class_to_build in self._prepared and cache:
            return self._prepared[class_to_build]  # type: ignore
        my_class_name = class_to_build.__name__

        init_args = inspect.getfullargspec(class_to_build)
        if init_args.defaults is not None:
            self._disallow_kwargs(f"build class '{class_to_build.__name__}'")

        # ignore the first argument because that is just `self`
        build_arguments = init_args.args[1:]
        if not build_arguments:
            if hasattr(class_to_build, "injectable_properties"):
                class_to_build.injectable_properties(self)
            built_value = class_to_build()
            if cache:
                self._prepared[class_to_build] = built_value  # type: ignore
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
                f"Circular dependencies detected while building '{my_class_name}' because '"
                + f"{my_class_name} is a dependency of both '{context}' and {original_context_label}"
            )

        self._building[class_id] = context
        # Turn on caching when building the automatic dependencies that get injected into a class constructor
        args = [
            self.build_argument(build_argument, init_args.annotations.get(build_argument, None), context=my_class_name, cache=True)
            for build_argument in build_arguments
        ]

        del self._building[class_id]

        built_value = class_to_build(*args)
        if hasattr(built_value, "injectable_properties"):
            built_value.injectable_properties(self)
        if cache:
            self._prepared[class_to_build] = built_value  # type: ignore
        return built_value

    def build_class_from_type_hint(self, argument_name: str, class_to_build: type | None, context: str='', cache: bool=True) -> Any | None:
        """
        Build an argument from a type hint.

        Note that in many cases we can't actually build the thing.  It may be a type hint of a built-in or some other value
        that we're not configured to deal with.  In that case, just return None and the calling method will deal with it.

        This follows the resolution order defined in the docblock of the Di class.
        """

        # these first checks just verify that it is something that we can actually build
        if not class_to_build:
            return None
        if not callable(class_to_build):
            return None
        if inspect.isabstract(class_to_build):
            return None

        # then first things first: check our class overrides
        if class_to_build in self._class_overrides_by_class:
            return self.build_class(self._class_overrides_by_class[class_to_build], context=context, cache=cache)

        # next check our additional config classes
        built_value = None
        can_cache = False
        for index in range(len(self._additional_configs) - 1, -1, -1):
            additional_config = self._additional_configs[index]
            if not additional_config.can_build_class(class_to_build):
                continue

            built_value = additional_config.build_class(class_to_build, argument_name, self, context=context)
            can_cache = additional_config.can_cache_class(class_to_build, self, context)
            break

        # a small handful of predefined classes
        if class_to_build in self._predefined_classes_name_map:
            dependency_name = self._predefined_classes_name_map[class_to_build]
            built_value = call_function(self, f"provide_{dependency_name}")
            can_cache = self.can_cache(dependency_name, context if context else "")

        # finally, if we found something, cache and/or return it
        if built_value is not None:
            if cache and can_cache:
                self._prepared[class_to_build] = built_value  # type: ignore
            return built_value

        # last but not least we build the class itself as long as it has been imported into the Di system
        if class_to_build in self._classes:
            return self.build_class(class_to_build, context=context, cache=cache)

        return None

    def call_function(self, callable_to_execute: Callable, **kwargs):
        """
        Calls a function, building any positional arguments and providing them.

        Any kwargs passed to call_function will populate the equivalent dependencies.

        ```
        from clearskies.di import Di

        di = Di(bindings={"some_name": "hello"})
        def my_function(some_name, some_other_name):
            print(f"{some_name} {some_other_value}") # prints 'hello world'
        di.call_function(my_function, some_other_value="world")
        ```
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
            else self.build_argument(arg, args_data.annotations.get(arg, None), context=callable_to_execute.__name__, cache=True)
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

    def can_cache(self, name: str, context: str) -> bool:
        """
        Control whether or not to cache a value built by the DI container.
        """
        if name == "now" or name == "utcnow":
            return False
        return True

    def provide_di(self):
        return self

    def provide_requests(self):
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["GET", "POST", "DELETE", "OPTIONS", "PATCH"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def provide_sys(self):
        import sys
        return sys

    def provide_environment(self):
        return Environment(os.getcwd() + "/.env", os.environ, {})

    def provide_connection_no_autocommit(self, connection_details):
        # I should probably just switch things so that autocommit is *off* by default
        # and only have one of these, but for now I'm being lazy.
        try:
            import pymysql
        except:
            raise ValueError("The cursor requires pymysql to be installed.  This is an optional dependency of clearskies, so to include it do a `pip install 'clear-skies[mysql]'`")

        return pymysql.connect(
            user=connection_details["username"],
            password=connection_details["password"],
            host=connection_details["host"],
            database=connection_details["database"],
            port=connection_details.get("port", 3306),
            ssl_ca=connection_details.get("ssl_ca", None),
            autocommit=False,
            connect_timeout=2,
            cursorclass=pymysql.cursors.DictCursor,
        )

    def provide_connection(self, connection_details):
        try:
            import pymysql
        except:
            raise ValueError("The cursor requires pymysql to be installed.  This is an optional dependency of clearskies, so to include it do a `pip install 'clear-skies[mysql]'`")

        return pymysql.connect(
            user=connection_details["username"],
            password=connection_details["password"],
            host=connection_details["host"],
            database=connection_details["database"],
            port=connection_details.get("port", 3306),
            ssl_ca=connection_details.get("ssl_ca", None),
            autocommit=True,
            connect_timeout=2,
            cursorclass=pymysql.cursors.DictCursor,
        )

    def provide_connection_details(self, environment):
        return {
            "username": environment.get("db_username"),
            "password": environment.get("db_password"),
            "host": environment.get("db_host"),
            "database": environment.get("db_database"),
        }

    def provide_cursor(self, connection):
        return connection.cursor()

    def provide_now(self):
        return datetime.datetime.now() if self._now is None else self._now

    def provide_utcnow(self):
        return datetime.datetime.now(datetime.timezone.utc) if self._utcnow is None else self._utcnow

    def provide_input_output(self):
        raise AttributeError(
            "The dependency injector requested an InputOutput but none has been configured.  Alternatively, if you directly called `di.build('input_output')` then try again with `di.build('input_output', cache=True)`"
        )

    def provide_oai3_schema_resolver(self):
        from clearskies import autodoc
        return autodoc.formats.oai3_json.OAI3SchemaResolver()

    def provide_uuid(self):
        import uuid
        return uuid

    def provide_secrets(self):
        return clearskies.secrets.Secrets()

    def provide_memory_backend_default_data(self):
        return {}
