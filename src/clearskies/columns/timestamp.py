from typing import List


from clearskies import configs, parameters_to_properties
from clearskies.columns import Datetime


class Timestamp(Datetime):
    # whether or not to include the milliseconds in the timestamp
    include_microseconds = configs.Boolean(default=False)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        include_milliseconds: Optional[bool] = False,
        date_format: Optiona[str] = None,
        default_date: Optional[str] = None,
        validators: Union[Callable, Validator, BindingValidator, List[Union[Callable, Action, BindingAction]]] = [],
        is_readable: bool = True,
        is_writeable: bool = False,
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
