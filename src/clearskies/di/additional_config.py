from typing import Any, Dict, Optional
class AdditionalConfig:
    """
    The AdditionalConfig object provides a more flexible/programmatic way to re-define a dependency for injection.

    To provide dependencies via the AdditionalConfig class, extend it and declare one or more methods with names
    that start with `provide_`.  Everything after `provide_` in the function name becomes a recognized dependency
    injection name.  These provide methods can declare their own dependencies and they will be provided by the
    dependency injection container - even if declared in the same AdditionalConfig class.

    Note that AdditionalConfig objects take precedence over any "standard" dependencies.

        Example:
            The following example uses the additional_configs kwarg on the context constructor, which is passed into
            to the constructor of the dependency injection container.

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
