from clearskies.configs import config


class StringList(config.Config):
    """
    This is for a configuration that should be a list of strings.

    This is different than SelectList, which also accepts a list of strings, but
    valdiates that all of those values match against an allow list.
    """

    def __set__(self, instance, value: list[str]):
        if value is None:
            return

        if not isinstance(value, list):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a list parameter"
            )
        for index, item in enumerate(value):
            if not isinstance(item, str):
                error_prefix = self._error_prefix(instance)
                raise TypeError(
                    f"{error_prefix} attempt to set a value of type '{item.__class__.__name__}' for item #{index + 1}.  A string was expected."
                )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> list[str]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
