from typing import Callable

import clearskies.typing
from clearskies.columns import BelongsTo
from clearskies import parameters_to_properties


class BelongsToSelf(BelongsTo):
    """
    This is a standard BelongsTo column except it's used in cases where the model relates to itself.

    This exists because a model can't refer to itself inside it's own class definition.  There are
    workarounds, but having this class is usually quicker for the developer.

    The only difference between this and BelongsTo is that you don't have to provide the parent class.

    See also HasManySelf
    """
    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        readable_parent_columns: list[str] = [],
        join_type: str | None = None,
        where: clearskies.typing | list[clearskies.typing] = []
        default: str | None = None,
        setable: str | Callable | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_temporary: bool = False,
        validators: clearskies.typing.validators | list[clearskies.typing.validators] = [],
        on_change_pre_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_post_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_save_finished: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
    ):
        pass
