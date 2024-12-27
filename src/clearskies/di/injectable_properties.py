from __future__ import annotations
from typing import Any, TYPE_CHECKING
from clearskies.di.injectable import Injectable

if TYPE_CHECKING:
    from clearskies.di import Di

class InjectableProperties:
    """
    Allows you to provide dependencies via properties rather than constructor arguments

    This class allows you to specify dependencies by setting them as class properties instead of constructor
    arguments.  This is common in clearskies as it helps make easily reusable classes - configuration can
    go in the constructor of the class, allowing the developer to directly instantiate it, and then the DI system
    will come by afterwards and provide the necessary dependencies.

    After adding InjectableProperties as a parent of your class, you have two ways to specify your dependencies:

     1. By using the classes in the `clearskies.di.inject.*`module.
     2. By directly attaching objects which also use the `InjectableProperties` class.

    Here's an example:

    ```
    import clearskies
    from clearskies import parameters_to_properties

    class ReusableClass(clearskies.Configurable, clearskies.di.injectable_properties):
        my_int = clearskies.config.Integer(required=True)
        some_number = clearskies.di.inject.by_name('some_number')

        @parameters_to_properties.parameters_to_properties
        def __init__(self, my_int: int):
            self.finalize_and_validate_configuration()

        def my_value(self) -> int:
            return my_int*some_number

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
    print(my_other_class.my_value()) # prints 100
    ```
    """
    _injectable_descriptors: list[str] = []
    _injectable_properties: list[str] = []
    _injectable_properties_found = False

    def injectable_properties(self, di: Di):
        cls = self.__class__
        if not cls._injectable_properties_found:
            cls._injectable_descriptors = []
            cls._injectable_properties = []
            for attribute_name in dir(self):
                # Per the docs above, we want to inject properties for one of two things: the injectables from clearskies.di.inject,
                # and any object that itself extends this class.  This is mildly tricky because the injectables are descriptors, and
                # so we get them using getattr on the class, while if it's not a descriptor, then we want to use getattr on self.
                # The important part here is that we modify descriptors at the class level, so the actual injected values have to
                # be stored in self, and not in the descriptor object.  When it's not a descriptor, then we can modify the object
                # directly (since we're operating at the object level, not class level).  Either way, while we go, let's keep track
                # of what our dependencies are and which ones are cached, so we only have to list the objects attributes the first time.
                attribute = getattr(self.__class__, attribute_name)

                if issubclass(attribute.__class__, Injectable):
                    cls._injectable_descriptors.append(attribute_name)
                    continue

                if hasattr(attribute, 'injectable_properties'):
                    cls._injectable_properties.append(attribute_name)
                    continue
            cls._injectable_properties_found = True

        for attribute_name in cls._injectable_properties:
            getattr(self, attribute_name).injectable_properties(di)

        for attribute_name in cls._injectable_descriptors:
            getattr(cls, attribute_name).set_di(di)
