from typing import Callable, List, Optional, Union


from clearskies import configs, parameters_to_properties, ColumnConfig
from clearskies.bindings import Action as BindingAction
from clearskies.actions import Action
from clearskies.bindings import Validator as BindingValidator
from clearskies.columns.validators import Validator


class BelongsTo(ColumnConfig):
    parent_model_class = configs.ModelClass(required=True)
    model_column_name = configs.String()
    readable_parent_columns = configs.ReadableModelColumns("parent_model_class")
    join_type = configs.select(["LEFT", "INNER", "RIGHT"], default="LEFT")
    where = configs.Conditions()

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        parent_model_class,
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
