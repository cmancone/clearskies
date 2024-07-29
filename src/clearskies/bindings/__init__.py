"""
These class all exist to solve a very specific problem introduced by dependency injection (DI).

The nature of dependency injection means that the developer can no longer instantiate many classes
themselves, since they would then need to provide the necessary dependencies themselves.  This is
not a problem when you talk about actual dependencies that are injected into your code by the DI
container.  For instance, consider this class:

```
def MyClass:
    def __init__(self, dependency_1, dependency_2):
        pass
```

Since `dependency_1` and `dependency_2` are built by the DI container and provided for you,
you don't care what their dependencies are and everything works great.  However, this doesn't work out
when you want to define things a bit more dynamically, which happens throughout clearskies.  There's
a common need to specify classes in places other than the constructor, as well as a need to have reusable
classes that can be used in different contexts with different configuration.  These can be challenging
if all you can do is inject dependencies in the constructor.  If that is your only option, you are
effectively forced to have a centralized configuration store where you define everything, and that gets
tedious, error prone, and hard to maintain.

These classes (generally referred to as bindings) solve this issue by allowing you to specify a class
that you wish to use along with it's configuration.  The DI container can then turn that into an actual instance.
In general *you* don't have to worry about using the DI container to make the instance: rather, portions
of clearskies are built to accept bindings, and they will then convert them to actual classes as needed.
The end result is that the developer gets more flexibility in deciding what classes to use, as well as their
configuration, and internally everything still relies on dependency configuration.

The way this works in practice is fairly straight-forward.  The base binding class is a simple class that accepts a
class-to-be-built and (optionally) its configuration.  The class-to-be-built then declares its dependencies
in the `__init__` method as always, and also specifies a `configuration` method that will accept whatever
configuration options are specified by the binding.  Here's an example of a class-to-be-built that is then
wrapped up in a binding:

```
import clearskies

class MyConfigurableClass:
    @clearskies.parameters_to_properties
    def __init__(self, dependency_1):
        pass

    @clearskies.parameters_to_properties
    def configure(self, arg_1, kwarg_1=None, kwarg_2=None):
        pass

my_configuable_class_binding = clearskies.bindings.Binding(
    MyConfigurableClass,
    arg_1_value,
    kwarg_1='some_value',
    kwarg_2='another_value',
)
```

`my_configuable_class_binding` keeps track of the desired class (`MyConfigurableClass`) and its configuration.
When the application is ready to work with it, `my_configuable_class_binding` can be passed into `di.build()`,
which will then construct an instance of `MyConfigurableClass`, providing the dependencies declared in the
`__init__` method just like it always would, and then it will call the configure method on the new instance
and pass along any args and kwargs passed into the Binding class.  in other words, building off of the above
example, the following code:

```
configured_class = di.build(my_configuable_class_binding)
```

is the equivalent of:

```
dependency_1 = di.build("dependency_1")
configured_class = MyConfigurableClass(dependency_1)
configured_class.configure(
    arg_1_value,
    kwarg_1='some_value',
    kwarg_2='another_value',
)
```

To aid with typing and IDE auto fill, all of this is usually wrapped up in a function that returns a binding. e.g.:

```
import clearskies

def my_configurable_class(arg_1, kwarg_1=None, kwarg_2=None):
    return clearskies.bindings.Binding(
        MyConfigurableClass,
        arg_1,
        kwarg_1='some_value',
        kwarg_2='another_value',
    )
```

Finally, a few specifc sub-classes of `Binding` are created to enable typing throughout the framework.
"""

from .action import Action
from .binding import Binding
from .validator import Validator

__all__ = [
    "Action",
    "Binding",
    "Validator",
]
