import datetime
from typing import Optional

from clearskies.columns import datetime
from clearskies import configs, parameters_to_properties


class Updated(datetime.Datetime):
    in_utc = configs.Boolean(default=True)
    is_writeable = configs.Boolean(default=False)
    include_microseconds = configs.Boolean(default=False)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        in_utc: bool = True,
        date_format: Optional[str] = None,
        default_date: Optional[str] = None,
        include_microseconds: Optional[bool] = False,
        validators: Union[Callable, Validator, BindingValidator, List[Union[Callable, Action, BindingAction]]] = [],
        is_readable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: Union[Callable, Action, BindingAction, List[Union[Callable, Action, BindingAction]]] = [],
        on_change_post_save: Union[Callable, Action, BindingAction, List[Union[Callable, Action, BindingAction]]] = [],
        on_change_save_finished: Union[
            Callable, Action, BindingAction, List[Union[Callable, Action, BindingAction]]
        ] = [],
        default: Optional[str] = None,
        setable: Optional[str] = None,
        created_by_source_type: str = "",
        created_by_source_key: str = "",
    ):
        pass
