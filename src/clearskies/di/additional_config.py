from typing import Any


class AdditionalConfig:
    """
    This class allows you to add additional names to the Di container.

    The idea here is that you extend the AdditonalConfig class and attach as many
    `provide_*` methods to the class as you want.  This allows the developer to declare a number of
    dependencies and easily attach them to the Di container in one go - helpful for modules that
    come with a variety of things that they want to make available to developers.

    When an AdditionalConfig instance is attached to the Di container, the container (in essence) finds all the
    `provide_*` methods in the class and registers the corresponding name in the Di container - e.g. if you have
    a method called `provide_widget` then when a class or function requests an argument named `widget`
    from the Di container, the container will call the `provide_widget` method on your instance and pass along
    the return value to the thing that requested a `widget`. The `provide_*` methods can declare their own
    dependencies, including ones declared in the same `AdditionalConfig` class (they just can't be circular, of course).

    As always, keep in mind the priority of dependency injection names (see the `clearskies.di.Di` class for full
    details).  If two `AdditionalConfig` objects declare a `provide_*` method with the same name, then the Di
    system will call the method for the `AdditionalConfig` object that was added last.

    By default the Di system caches all values.  If you have a dependency that shouldn't be cached, you can
    extend the `can_cache` method and have it return True/False depending on the name and context.

    Example:
    ```python
    from clearskies.di import Di, AdditionalConfig


    class MyAdditionalConfig(AdditionalConfig):
        def provide_inner_dependency(self):
            return 5

        def provide_important_thing(self, inner_dependency):
            return inner_dependency * 10


    class AnotherAdditionalConfig(AdditionalConfig):
        def provide_inner_dependency(self):
            return 10


    di = Di(additional_configs=[MyAdditionalConfig(), AnotherAdditionalConfig()])
    # Equivalent:
    # di = Di()
    # di.add_addtional_configs([MyAdditionalConfig(), AnotherAdditionalConfig()])


    def my_function(important_thing):
        print(important_thing)  # prints 100
    ```
    """

    def can_cache(self, name: str, di, context: str) -> bool:
        """
        Cache control.

        The Di container caches values by default, but this method allows you to override that.
        After fetching an object from the AdditionalConfig class, the Di container will call this method to
        determine whether or not to cache  it.  `name` will be the name of the Di value that was built, and
        context will be the name of the class that the value was built for.  You then return True/False.

        Note that this controls whether or not to cache the returned value, not whether or not to check the
        cache for a value.  The importance is that, once there is a value in the cache, that will be reused
        for all future requests for that name.  Example:

        ```python
        from clearskies.di import Di, AdditionalConfig
        import secrets


        class MyAdditionalConfig(AdditionalConfig):
            def provide_random_number_not_cached(self):
                return secrets.randbelow(100)

            def provide_random_number_cached(self):
                return secrets.randbelow(100)

            def can_cache(self, name, context=None):
                return name == "random_number_not_cached"


        di = Di(additional_configs=MyAdditionalConfig())


        def my_function(random_number_cached, random_number_not_cached):
            print(random_number_cached)
            print(random_number_not_cached)


        di.call_function(my_function)
        di.call_function(my_function)
        di.call_function(my_function)
        di.call_function(my_function)

        # This prints something like:
        # 58
        # 12
        # 58
        # 14
        # 58
        # 41
        ```
        """
        return True

    def can_build(self, name):
        return hasattr(self, f"provide_{name}")

    def build(self, name, di, context=None):
        if not hasattr(self, f"provide_{name}"):
            raise KeyError(
                f"AdditionalConfig class '{self.__class__.__name__}' cannot build requested dependency, '{name}'"
            )

        return di.call_function(getattr(self, f"provide_{name}"))

    def can_build_class(self, class_to_check: type) -> bool:
        """Return True/False to denote if this AdditionalConfig class can provide a given class."""
        return False

    def build_class(self, class_to_provide: type, argument_name: str, di, context: str = "") -> Any:
        """Return the desired instance of a given class."""
        pass

    def can_cache_class(self, class_to_build: type, di, context: str) -> bool:
        """Control whether or not the Di container caches the instance after building a class."""
        return False
