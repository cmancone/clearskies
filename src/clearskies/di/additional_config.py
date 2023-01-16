from typing import Any, Dict, Optional
class AdditionalConfig:
    """
    The AdditionalConfig object provides a more flexible/programmatic way to re-define a dependency for injection.

    To provide dependencies via the AdditionalConfig class, extend it and declare one or more methods with names
    that start with `provide_`.  Everything after `provide_` in the function name becomes a recognized dependency
    injection name.  These provide methods can declare their own dependencies and they will be provided by the
    dependency injection container - even if declared in the same AdditionalConfig class.

    Example:
        The following example declares an AdditionalConfig object and shows how to use it in a simple application.
        It prints out "this is a simple example"::

            class MyDependencies(clearskies.di.AdditionalConfig):
                def provide_my_first_dependency(self):
                    return 'simple example'
                def provide_my_second_dependency(self, my_first_dependency):
                    return 'this is a ' + my_first_dependency

            def my_function(my_second_dependency):
                print(my_second_dependency)

            cli = clearskies.contexts.cli(
                my_function,
                additional_configs=[MyDependencies()],
            )
            cli()

    Note that an instance is passed to the dependency injection container - not the class.
    """
    _config: Dict[Any, Any] = {}

    def __init__(self, config: Optional[Dict[Any, Any]] = None):
        self.config = config if config else {}

    def can_build(self, name: str) -> bool:
        """
        Return true/false to denote if this AdditionalConfig instance can provide a specific dependency.

        Args:
            name: The name of the dependency to check
        """
        return hasattr(self, f'provide_{name}')

    def build(self, name: str, di: Any, context: Optional[str] = None) -> Any:
        """
        Builds the dependency given by "name".  The class must have a corresponding "provide_[name]" method.

        Args:
            name: The name of the dependency to build.
            di: The dependency injection container.
            context: Information about the dependency this is required for.
        """
        if not hasattr(self, f'provide_{name}'):
            raise KeyError(
                f"AdditionalConfig class '{self.__class__.__name__}' cannot build requested dependency, '{name}'"
            )

        return di.call_function(getattr(self, f'provide_{name}'))
