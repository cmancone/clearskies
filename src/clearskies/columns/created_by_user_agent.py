import clearskies.typing
from clearskies import column_config
from clearskies import configs, parameters_to_properties


class CreatedByUserAgent(column_config.ColumnConfig):
    """
    This column will automatically take user agent from the client and store it in the model upon creation.

    If the user agent isn't available from the context being executed, then you may end up with an error
    (depending on the context).  This is a good thing if you are trying to consistely provide audit information,
    but may be a problem if your model creation needs to happen more flexibly.
    """

    """
    Since this column is always populated automatically, it is never directly writeable.
    """
    is_writeable = configs.Boolean(default=False)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        is_readable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_post_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_save_finished: clearskies.typing.actions | list[clearskies.typing.actions] = [],
    ):
        pass
