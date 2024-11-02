from typing import List


from clearskies import configs, parameters_to_properties
from clearskies.columns import String


class Select(String):
    """ The allowed values. """
    allowed_values = clearskies.configs.StringList(default=True)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        allowed_values: List[str] = [],
        validators: Union[Callable, Validator, BindingValidator, List[Union[Callable, Action, BindingAction]]] = [],
        is_readable: bool = True,
        is_writeable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: Union[Callable, Action, BindingAction, List[Union[Callable, Action, BindingAction]]] = [],
        on_change_post_save: Union[Callable, Action, BindingAction, List[Union[Callable, Action, BindingAction]]] = [],
        on_change_save_finished: Union[
            Callable, Action, BindingAction, List[Union[Callable, Action, BindingAction]]
        ] = [],
        default: Str = None,
        created_by_source_type: str = '',
        created_by_source_key: str = '',
        model_column_name: Optional[str] = None,
        readable_parent_columns: Optional[list[str]] = None,
        join_type: Optional[str] = None,
        where: Optional[Union[str, Callable, List[Union[str, Callable]]]] = None
    ):
        pass
