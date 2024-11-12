from clearskies import column_config


class Uuid(column_config.ColumnConfig):
    is_writeable = configs.Boolean(default=False)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
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

