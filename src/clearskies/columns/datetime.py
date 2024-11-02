import datetime
from typing import Optional

from clearskies import column_config
from clearskies import configs, parameters_to_properties


class Datetime(column_config.ColumnConfig):
    date_format = configs.String(default="%Y-%m-%d %H:%M:%S")
    default_date = configs.String(default="0000-00-00 00:00:00")

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
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


    def __get__(self, instance, parent) -> datetime.datetime:
        if not instance:
            return self  # type: ignore

        return instance._data[self._my_name(instance)]

    def __set__(self, instance, value: datetime.datetime) -> None:
        instance._next_data[self._my_name(instance)] = value
