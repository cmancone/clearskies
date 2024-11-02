from typing import Callable, List, Optional, Union


from clearskies import configs, parameters_to_properties, ColumnConfig
from clearskies.bindings import Action as BindingAction
from clearskies.actions import Action
from clearskies.bindings import Validator as BindingValidator
from clearskies.columns.validators import Validator


class ManyToMany(ColumnConfig):
    """ The model class for the model that we are related to. """
    related_model_class = configs.ModelClass(required=True)

    """ The model class for the pivot table - the table used to record connections between ourselves and our related table. """
    pivot_model_class = configs.ModelClass(required=True)

    """ The name of the column in the pivot table that contains the id of records from our table. """
    own_column_name_in_pivot = configs.ModelToIdColumn()

    """ The name of the column in the pivot table that contains the id of records from the related table. """
    foreign_column_name_in_pivot = configs.ModelToIdColumn("related_model_class")

    """ The name of the pivot table (loaded automatically). """
    pivot_table = configs.ModelDestinationName("pivot_model_class")

    """ The list of columns to be loaded from the related models when we are converted to JSON. """
    readable_related_columns = configs.ReadableModelColumns("related_model_class")

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        related_model_class,
        pivot_model_class,
        own_column_name_in_pivot: str = "",
        foreign_column_name_in_pivot: str = "",
        readable_related_columns: List[str] = [],
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
