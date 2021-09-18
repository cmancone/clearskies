# Dependency Injection

The dependency injection system from clearskies is a name-based system, rather than type-based system.  This is partly because types will always be optional in Python, and partly because early versions of clearskies used [pinject](https://github.com/google/pinject), which is a name-based injection system.

Dependency injection settings can be configured at both the application and context level.  This allows you to set defaults for an application and then override them if necessary at run time.  In addition, there are a variety of ways to configure dependency injection, with a clear order priority to resolve conflicts.  Finally, clearskies can auto-load all the classes in your application to make dependency injection configuration as automated as possible.

## Name-based injection?

Name-based injection means that when clearskies is deciding what to inject for a function/contructor parameter, it looks at the actual parameter name rather than the parameter type.  Consider the following code:

```
import clearskies

def my_function(input_output, requests, now):
    print(input_output)
    print(requests)
    print(now)

cli_callable = clearskies.contexts.cli(my_function)
if __name__ == '__main__':
    cli_callable()
```

Since `my_function` is being executed by the clearskies context, clearskies provides all of its parameters via the dependency injection configuration.  This means that clearskies will check the dependency injection configuration for parameters named `requests`, `now`, and `input_output`.  In this example we haven't configured anything for our dependency injection container, but it just so happens that these are [standard dependencies](#standard-dependencies) that are always provided by clearskies.  If we run it, we'll get back something like this:

```
<clearskies.input_outputs.cli.CLI object at 0x7f66c23ba340>
<requests.sessions.Session object at 0x7f66c13d6580>
2021-09-18 13:27:45.904158
```

## Configuring Dependency Injection

There are probably too many ways to configure the dependency injection container.  In order of priority (highest priority items first):

1. ["di"](#1-di)
2. [Directly Binding Values](#2-directly-binding-values)
3. [Add Classes and Modules](#3-add-classes-and-modules)
4. [Additional Configuration Classes](#4-additional-configuration-classes)
5. [Pre-Defined Dependencies](#5-pre-defined-dependencies)

### 1. di

The name `di` is the only reserved keyword in the clearskies dependency injection system.  If you ask for a dependency with this name, clearskies will inject the current dependency injection container:

```
import clearskies

def my_function(di):
    print(di)

cli_callable = clearskies.contexts.cli(my_function)
if __name__ == '__main__':
    cli_callable()
```

Which would give you:

```
<clearskies.di.standard_dependencies.StandardDependencies object at 0x7ff642c0fca0>
```

Which is an instance of the [StandardDependencies class](../src/clearskies/di/standard_dependencies.py).

### 2. Directly Binding Values

The dependency injection container has a `bind` method that takes a name and value.  The contexts also have `bind` methods which pass calls along to the depenency injection container.  Finally, when building contexts or applications you can provide the `bindings` kwarg to pass a dictionary of bindings along into the dependency injection container.  This can include either "final" values or classes.  Keep in mind though that a later invocation of `bind` can override previous values:

```
import clearskies

class MyAwesomeClass:
    def __init__(self, some_other_value):
        self.some_other_value = some_other_value

    def print_my_value(self):
        print(self.some_other_value)

def my_function(my_favorite_number, my_favorite_letter, my_awesome_class):
    print(my_favorite_number)
    print(my_favorite_letter)
    my_awesome_class.print_my_value()

my_application = clearskies.Application(
    clearskies.handlers.Callable,
    {'callable': my_function},
    bindings={
        'my_awesome_class': MyAwesomeClass,
        'some_other_value': 'foo',
    },
)

cli_callable = clearskies.contexts.cli(
    my_application,
    bindings={
        'my_favorite_number': 5,
        'my_favorite_letter': 'A',
    },
)
cli_callable.bind('some_other_value', 'bar')
if __name__ == '__main__':
    cli_callable()
```

And if you ran this you would get:

```
5
A
bar
```

### 3. Add Classes and Modules

The dependency injection container has a method called `add_classes` that you can use to register additional classes for dependency injection.  When using it to register classes, you don't provide the name to inject it under.  Instead, clearskies just converts the class names to snake_case and automatically registers them with that name.

`add_modules` allows you to provide modules to inject.  However, it doesn't let you literally inject the modules.  Instead, it finds all classes in the modules and registers them with `add_classes`.

Both of these methods are exposed to the application and context via the `binding_classes` and `binding_modules` kwargs which accept a list of classes or modules:

```
import clearskies

class MyFirstClass:
    class_number = 1

class MySecondClass:
    class_number = 2

def my_function(my_first_class, my_second_class):
    print(my_first_class.class_number)
    print(my_second_class.class_number)

my_application = clearskies.Application(
    clearskies.handlers.Callable,
    {'callable': my_function},
    binding_classes=[MyFirstClass],
)

cli_callable = clearskies.contexts.cli(
    my_application,
    binding_classes=[MySecondClass],
)
if __name__ == '__main__':
    cli_callable()
```

Which prints:

```
`
2
```

**HOWEVER**, you probably don't have to do this.  by default clearskies will automatically find any imported classes and modules that are defined in a subdirectory of the current script, and import those, so actually this works exactly the same as the previous example:

```
import clearskies

class MyFirstClass:
    class_number = 1

class MySecondClass:
    class_number = 2

def my_function(my_first_class, my_second_class):
    print(my_first_class.class_number)
    print(my_second_class.class_number)

cli_callable = clearskies.contexts.cli(my_function)
if __name__ == '__main__':
    cli_callable()
```

### 4. Additional Configuration Classes

The dependency injection container allows you to provide additional classes that define dependencies by declaring methods named `provide_[name]` where `[name]` is the name of the dependency to inject.  clearskies will call the appropriate `provide` method when it is needed, and when it does so, it will also provide any parameters needed by the method.

You can specify these classes via the `add_additional_configs` methods on the dependency injection container, which is exposed via the `additional_configs` kwarg when building a context or an application.  This kwarg accepts a list of either classes and/or objects:

```
import clearskies

class MoarConfiguration(clearskies.di.AdditionalConfig):
    def provide_double_it(self, my_number):
        return my_number*2

def my_function(my_number, double_it):
    print(my_number)
    print(double_it)

cli_callable = clearskies.contexts.cli(
    my_function,
    bindings={'my_number': 4},
    additional_configs=[MoarConfiguration],
)
if __name__ == '__main__':
    cli_callable()
```

Which prints:

```
4
8
```

### 5. Pre-Defined Dependencies

## Standard Dependencies
