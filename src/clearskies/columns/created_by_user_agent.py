from __future__ import annotations
import datetime
from typing import Any, TYPE_CHECKING

import clearskies.typing
from clearskies.columns.string import String
from clearskies import configs
import clearskies.parameters_to_properties

if TYPE_CHECKING:
    from clearskies import Model

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
    _descriptor_config_map = None

    _allowed_search_operators = ["=", "in", "is not null", "is null", "like"]

    @clearskies.parameters_to_properties.parameters_to_properties
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

    def pre_save(self, data: dict[str, Any], model: Model) -> dict[str, Any]:
        if model:
            return data
        input_output = self.di.build("input_output", cache=True)
        data = {**data, self.name: input_output.get_request_header("user-agent")}
        if self.on_change_pre_save:
            data = self.execute_actions_with_data(self.on_change_pre_save, model, data)
        return data
