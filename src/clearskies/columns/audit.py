from typing import Callable, List, Optional, Union


from clearskies import configs, parameters_to_properties
from clearskies.bindings import Action as BindingAction
from clearskies.actions import Action
from clearskies.bindings import Validator as BindingValidator
from clearskies.columns.validators import Validator
from clearskies.columns import HasMany


class Audit(HasMany):
    audit_model_class = configs.ModelClass(required=True)
    child_model_class = configs.Model()
    exclude_columns = configs.ModelColumns()
    mask_columns = configs.ModelColumns()
    foreign_column_name = configs.ModelColumn("audit_model_class")
    readable_child_columns = configs.ReadableModelColumns("audit_model_class", default=["resource_id", "action", "data", "created_at"])

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        audit_model_class: Optional[str] = None,
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
    ):
        self.child_model_class = self.audit_model_class
