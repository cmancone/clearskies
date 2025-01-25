from typing import Callable

import clearskies.typing
from clearskies.columns.belongs_to_id import BelongsToId
from clearskies import parameters_to_properties


class BelongsToSelf(BelongsToId):
    """
    This is a standard BelongsToId column except it's used in cases where the model relates to itself.

    This exists because a model can't refer to itself inside it's own class definition.  There are
    workarounds, but having this class is usually quicker for the developer.

    The only difference between this and BelongsToId is that you don't have to provide the parent class.

    See also HasManySelf
    """

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        readable_parent_columns: list[str] = [],
        join_type: str | None = None,
        where: clearskies.typing.condition | list[clearskies.typing.condition] = [],
        default: str | None = None,
        setable: str | Callable | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_searchable: bool = True,
        is_temporary: bool = False,
        validators: clearskies.typing.validator | list[clearskies.typing.validator] = [],
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
        created_by_source_strict: bool = True,
    ):
        pass

    def finalize_configuration(self, model_class, name) -> None:
        """
        Finalize and check the configuration.

        This is an external trigger called by the model class when the model class is ready.
        The reason it exists here instead of in the constructor is because some columns are tightly
        connected to the model class, and can't validate configuration until they know what the model is.
        Therefore, we need the model involved, and the only way for a property to know what class it is
        in is if the parent class checks in (which is what happens here).
        """
        self.parent_model_class = model_class
        super().finalize_configuration(model_class, name)
