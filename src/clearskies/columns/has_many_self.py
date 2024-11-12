import clearskies.typing
from clearskies import parameters_to_properties
from clearskies.columns import HasMany


class HasManySelf(HasMany):
    """
    This is just like the HasMany column, but is used when the model references itself.

    This exists because a model can't refer to itself inside it's own class definition.  There are
    workarounds, but having this class is usually quicker for the developer.

    The only difference between this and HasMany is that you don't have to provide the child class.

    See also BelongsToSelf.
    """

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        foreign_column_name: str | None = None,
        readable_child_columns: list[str] = [],
        where: clearskies.typing.condition | list[clearskies.typing.condition] = [],
        is_readable: bool = True,
        on_change_pre_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_post_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_save_finished: clearskies.typing.actions | list[clearskies.typing.actions] = [],
    ):
        pass
