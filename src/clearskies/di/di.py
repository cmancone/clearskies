from ..binding_config import BindingConfig
import inspect
import re
import sys
import os


class DI:
    _bindings = None
    _building = None
    _classes = None
    _prepared = None
    _added_modules = None

    def __init__(self, classes=None, modules=None, bindings=None):
        self._bindings = {}
        self._prepared = {}
        self._classes = {}
        self._building = {}
        self._added_modules = {}
        if classes is not None:
            self.add_classes(classes)
        if modules is not None:
            self.add_modules(modules)
        if bindings is not None:
            for (key, value) in bindings.items():
                self.bind(key, value)

    def add_classes(self, classes):
        if inspect.isclass(classes):
            classes = [classes]
        for add_class in classes:
            name = self._camel_case_to_snake_case(add_class.__name__)
            #if name in self._classes:
                ## if we're re-adding the same class twice then just ignore it.
                #if id(add_class) == self._classes[name]['id']:
                    #continue

                ## otherwise throw an exception
                #raise ValueError(f"More than one class with a name of '{name}' was added")

            self._classes[name] = {'id': id(add_class), 'class': add_class}

    def add_modules(self, modules, root=None, is_root=True):
        if inspect.ismodule(modules):
            modules = [modules]

        for module in modules:
            module_id = id(module)
            if is_root:
                root = os.path.dirname(module.__file__)
            root_len = len(root)
            if module_id in self._added_modules:
                continue
            self._added_modules[module_id] = True

            for (name, item) in module.__dict__.items():
                if inspect.isclass(item):
                    self.add_classes([item])
                if inspect.ismodule(item):
                    if not hasattr(item, '__file__'):
                        continue
                    child_root = os.path.dirname(module.__file__)
                    if child_root[:root_len] != root:
                        continue
                    if module.__name__ == 'clearskies':
                        break
                    self.add_modules([item], root=root, is_root=False)

    def bind(self, key, value):
        if key in self._building:
            raise KeyError(f"Attempt to set binding for '{key}' while '{key}' was already being built")
        self._bindings[key] = value
        if key in self._prepared:
            del self._prepared[key]

    def build(self, thing, context=None, cache=True):
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

    def _camel_case_to_snake_case(self, string):
        return re.sub(
            '([a-z0-9])([A-Z])', r'\1_\2',
            re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
        ).lower()

    def build_from_name(self, name, context=None, cache=True):
        """
        Builds a dependency based on its name

        Order of priority:
          1. 'di' (aka self)
          2. Already prepared things
          3. Things set via `bind(name, value)`
          4. Method on DI class called `provide_[name]`
          5. Class via add_classes or add_modules
        """
        if name == 'di':
            return self

        if name in self._prepared and cache:
            return self._prepared[name]

        if name in self._bindings:
            built_value = self.build(self._bindings[name], context=context)
            if cache:
                self._prepared[name] = built_value
            return built_value

        if hasattr(self, f'provide_{name}'):
            built_value = self.call_function(getattr(self, f'provide_{name}'))
            if cache:
                self._prepared[name] = built_value
            return built_value

        if name in self._classes:
            built_value = self.build_class(self._classes[name]['class'], context=context)
            if cache:
                self._prepared[name] = built_value
            return built_value

        context_note = f" for {context}" if context else ''
        raise ValueError(
            f"I was asked to build {name}{context_note} but there is no added class, configured binding, " + \
            f"or a corresponding 'provide_{name}' method for this name."
        )


    def build_class(self, class_to_build, context=None, name=None, cache=True):
        """
        Builds a class

        The class constructor cannot accept any kwargs.   See self._disallow_kwargs for more details
        """
        if name is None:
            name = self._camel_case_to_snake_case(class_to_build.__name__)
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
        args = [
            self.build_from_name(build_argument, context=class_to_build.__name__)
            for build_argument
            in build_arguments
        ]
        del self._building[class_id]

        built_value = class_to_build(*args)
        if cache:
            self._prepared[name] = built_value
        return built_value

    def call_function(self, callable_to_execute, **kwargs):
        """
        Calls a function, building any positional arguments and providing them.

        Any kwargs passed to call_function will be passed along to the callable in question
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
            self.build_from_name(call_argument, context=callable_to_execute.__name__)
            for call_argument
            in call_arguments
        ]

        return callable_to_execute(*args, **kwargs)

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
        if 'modules' in bindings:
            modules = bindings['modules']
            del bindings['modules']

        di = cls(classes=binding_classes, modules=modules, bindings=bindings)
        return di
