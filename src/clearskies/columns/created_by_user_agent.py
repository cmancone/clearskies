import clearskies.typing
from clearskies.columns.string import String
from clearskies import configs, parameters_to_properties


class CreatedByUserAgent(String):
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

    _allowed_search_operators = ["=", "in", "is not null", "is null", "like"]

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        is_readable: bool = True,
        is_searchable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
    ):
        pass
