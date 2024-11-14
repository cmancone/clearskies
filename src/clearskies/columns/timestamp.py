from typing import Callable


from clearskies import configs, parameters_to_properties
from clearskies.columns import Datetime


class Timestamp(Datetime):
    """
    A timestamp column.

    The difference between this and the datetime column is that this stores the datetime
    as a standard unix timestamp - the number of seconds since the unix epoch.

    Also, this ALWAYS assumes the timezone for the timestamp is UTC
    """
    # whether or not to include the milliseconds in the timestamp
    include_microseconds = configs.Boolean(default=False)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        include_microseconds: bool = False,
        default: datetime.datetime | None = None,
        setable: datetime.datetime | Callable[..., datetime.datetime] | None = None,
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
