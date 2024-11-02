from typing import Callable, List, Optional, Union


from clearskies import configs, parameters_to_properties
from clearskies.columns import ManyToMany
from clearskies.bindings import Action as BindingAction
from clearskies.actions import Action
from clearskies.bindings import Validator as BindingValidator
from clearskies.columns.validators import Validator


class ManyToManyWithData(ManyToMany):
    """ The list of columns in the pivot model that can be set when saving data. """
    setable_columns = configs.ReadableModelColumns("pivot_model_class")

    """
    Complicated, but probably should be false.

    Sometimes you have to provide data from the related model class in your save data so that
    clearskies can find the right record.  Normally, this lookup column is not persisted to the
    pivot table, because it is assumed to only exist in the related table.  In some cases though,
    you may want it in both, in which case you can set this to true.
    """
    persist_unique_lookup_column_to_pivot_table = configs.Boolean(default=False)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        related_model_class,
        pivot_model_class,
        own_column_name_in_pivot: str = "",
        foreign_column_name_in_pivot: str = "",
        readable_related_columns: List[str] = [],
        setable_columns: List[str] = [],
        persist_unique_lookup_column_to_pivot_table: bool = False,
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
