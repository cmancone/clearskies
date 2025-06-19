# About

There are all sorts of things in clearskies that need to be configured - handlers, columns, models, etc...  `configurable.Configurable` works together with the config classes to make this happen.  The idea is that something that needs to be configured extends `Configurable` and then declares configs as properties.  A simple example:

```python
class ConfigurableThing(configurable.Configurable):
    my_name = config.String(required=True)
    is_required = config.Boolean(default=False)
    some_option = config.Select(allowed_values=["option 1", "option 2", "option 3"])
```

We've declared three configuration options for our `ConfigurableThing` class:

 1. `my_name` which is a string and must be set
 2. `is_required` which is a boolean and defaults to `False`
 3. `some_option` which is a string and must be one of `[None, "option 1", "option 2", "option 3"]`

However, our example above is missing one important thing: actually setting these values.  They act like standard descriptors, so with just the above code you could:

```python
configruable_thing = ConfigurableThing()
configruable_thing.my_name = "Jane Doe"
configruable_thing.is_required = True
configruable_thing.some_option = "option 2"
```

Typically though you need a well defined way to set these values **AND** the class must call `super().finalize_and_validate_configuration()` once the configuration is set.  This is because many of the validations are only possible after all the configs are set, so the configurable class treats the process of setting the configuration as a one-time, monolithic process: you set the configs, validate everything, and then use the config.  It's *NOT* the goal to continually change the configuration for an object after creation.  The simplest way to do this would be in the constructor:

```python
class ConfigurableThing(configurable.Configurable):
    my_name = config.String(required=True)
    is_required = config.Boolean(default=False)
    some_option = config.Select(allowed_values=["option 1", "option 2", "option 3"])

    def __init__(self,
        my_name: str,
        is_required: bool=False,
        some_option: str=None,
    ):
        self.my_name = my_name
        self.is_required = is_required
        self.some_option = some_option

        super().finalize_and_validate_configuration()
```

However, this doesn't always work because your class may be constructed via the dependency injection system.  In this case, the constructor must be reserved for injecting the necessary dependencies.  In addition, the object won't be constructed directly via code, so it's not possible to specify the configuration options there.  In this case, config values can be shifted to the `configure` method and you can use a binding config:

```python
class ConfigurableThing(configurable.Configurable):
    my_name = config.String(required=True)
    is_required = config.Boolean(default=False)
    some_option = config.Select(allowed_values=["option 1", "option 2", "option 3"])

    def __init__(self, some_dependency, other_dependency):
        self.some_dependency = some_dependency
        self.other_dependency = other_dependency

    def configure(self,
        my_name: str,
        is_required: bool=False,
        some_option: str=None,
    ):
        self.my_name = my_name
        self.is_required = is_required
        self.some_option = some_option

        super().finalize_and_validate_configuration()

context = clearskies.contexts.cli(
    SomeApplication,
    bindings={
        "configurable_thing": clearskies.bindings.Binding(ConfigurableThing, my_name="hey", is_required=Flase, some_option="option 2"),
    }
)
```

Note that we've lost our strong typing when creating the binding, but that can be fixed by extending the binding config:

```python
class ConfigurableThing:
    """ See above """

class ConfigurableThingBinding(clearskies.bindings.Binding):
    def __init__(
        self,
        my_name: str,
        is_required: bool=False,
        some_option: str=None,
    ):
        self.object_class = ConfigurableThing
        self.args = [my_name]
        self.kwargs = {"is_required": is_required, "some_option": some_option}

context = clearskies.contexts.cli(
    SomeApplication,
    bindings={
        "configurable_thing": ConfigurableThingBinding("hey", some_option="option 3")
    }
)
```

The primary example of classes that implement this pattern are the column config classes (`clearskies.columns.*`, but excluding `clearskies.columns.implementors`).  In this case the config and implementation are completely separated, so the configuration is set in the constructor instead of a separate `configure` method.

Validators, actions, and handlers also use the above config pattern, but those use the `Binding` pattern and so make use of a `configure` method.
