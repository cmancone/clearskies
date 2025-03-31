from __future__ import annotations
from typing import Any, TYPE_CHECKING
from clearskies.di.injectable import Injectable

if TYPE_CHECKING:
    from clearskies.di import Di

class InjectableProperties:
    """
    Fetch dependencies via properties rather than constructor arguments

    This class allows you to specify dependencies by setting them as class properties instead of constructor
    arguments.  This is common in clearskies as it helps make easily reusable classes - configuration can
    go in the constructor of the class, allowing the developer to directly instantiate it, and then the DI system
    will come by afterwards and provide the necessary dependencies.

    After adding InjectableProperties as a parent of your class, you have two ways to specify your dependencies:

     1. By using the classes in the `clearskies.di.inject.*`module.
     2. By directly attaching objects which also use the `InjectableProperties` class.

    The following table shows the dependencies that can be injected as properties via the clearskies.di.inject module:

    | Class                            | Type                                 | Result                                          |
    |----------------------------------|--------------------------------------|-------------------------------------------------|
    | clearskies.di.inject.ByClass     | N/A                                  | The specified class will be built               |
    | clearskies.di.inject.ByName      | N/A                                  | The specified dependnecy name will be built     |
    | clearskies.di.inject.Cursor      | N/A                                  | The PyMySQL cursor                              |
    | clearskies.di.inject.Di          | N/A                                  | The dependency injection container itself       |
    | clearskies.di.inject.Environment | clearskies.Environment               | The environment helper                          |
    | clearskies.di.inject.InputOutput | clearskies.input_outputs.InputOutput | The InputOutput object for the current request  |
    | clearskies.di.inject.Now         | datetime.datetime                    | The current time (no timezone)                  |
    | clearskies.di.inject.Requests    | requests.Session                     | A requests session                              |
    | clearskies.di.inject.Utcnow      | datetime.datetime                    | The current time (tzinfo=datetime.timezone.utc) |

    Note: now/utcnow are not cached, so you'll get the current time everytime you get a value out of the class property,
    unless a specific time has been set on the dependency injection container.

    Here's an example:

    ```
    import clearskies
    import time
    from clearskies import parameters_to_properties

    class MyOtherThing(clearskies.di.InjectableProperties):
        now = clearskies.di.inject.Now()

    class ReusableClass(clearskies.Configurable, clearskies.di.InjectableProperties):
        my_int = clearskies.configs.Integer(required=True)
        some_number = clearskies.di.inject.ByName('some_number')
        my_other_thing = clearskies.di.inject.ByClass(MyOtherThing)

        @parameters_to_properties
        def __init__(self, my_int: int):
            self.finalize_and_validate_configuration()

        def my_value(self) -> int:
            return self.my_int*self.some_number

    class MyClass(clearskies.di.InjectableProperties):
        reusable = ReusableClass(5)

    class MyOtherClass(clearskies.di.InjectableProperties):
        reusable = ReusableClass(10)

    di = clearskies.di.Di(
        bindings={
            "some_number": 10,
        }
    )

    my_class = di.build(MyClass)
    print(my_class.reusable.my_value()) # prints 50

    my_other_class = di.build(MyOtherClass)
    print(my_other_class.reusable.my_value()) # prints 100

    start = my_class.reusable.my_other_thing.now
    time.sleep(1)
    stop = my_class.reusable.my_other_thing.now
    print((stop - start).seconds) # prints 1
    ```
    """
    _injectables_loaded: dict[str, bool] = {}

    @classmethod
    def injectable_properties(cls, di: Di):
        # you would think that I would be able to just use a simple true/false flag attached to the class,
        # but I'm having this weird issue where (when I tried that) the flag was being shared between classes.
        # It shouldn't happen like that, but it is, so there is probably something subtle going on that I
        # haven't figured out yet, but this also works identitally, so :shrug:.
        # Also, keep track of the id of DI.  We use class level caching but tests often use multiple DI containers
        # in one run, which means that we need to re-inject dependencies if we get a new DI container
        cache_name = str(cls) + str(id(di))
        if cache_name in cls._injectables_loaded:
            return

        injectable_descriptors = []
        injectable_properties = []
        for attribute_name in dir(cls):
            # Per the docs above, we want to inject properties for one of two things: the injectables from clearskies.di.inject,
            # and any object that itself extends this class.  This is mildly tricky because the injectables are descriptors, and
            # so we get them using getattr on the class, while if it's not a descriptor, then we want to use getattr on self.
            # The important part here is that we modify descriptors at the class level, so the actual injected values have to
            # be stored in self, and not in the descriptor object.  When it's not a descriptor, then we can modify the object
            # directly (since we're operating at the object level, not class level).  Either way, while we go, let's keep track
            # of what our dependencies are and which ones are cached, so we only have to list the objects attributes the first time.
            attribute = getattr(cls, attribute_name)

            if di.has_class_override(attribute.__class__):
                setattr(cls, attribute_name, di.get_override_by_class(attribute))
                continue

            if issubclass(attribute.__class__, Injectable):
                attribute.set_di(di)
                continue

            if hasattr(attribute, 'injectable_properties'):
                attribute.injectable_properties(di)

        cls._injectables_loaded[cache_name] = True
