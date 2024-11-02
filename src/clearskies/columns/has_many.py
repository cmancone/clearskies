from typing import Callable, List, Optional, Union


from clearskies import configs, parameters_to_properties
from clearskies.bindings import Action as BindingAction
from clearskies.actions import Action
from clearskies.bindings import Validator as BindingValidator
from clearskies.columns.validators import Validator
from clearskies import column_config


class HasMany(column_config.ColumnConfig):
    """
    HasMany columns are not currently writeable.
    """
    is_writeable = configs.Boolean(default=False)

    """ The model class for the child table we keep our "many" records in. """
    child_model_class = configs.ModelClass(required=True)

    """
    The name of the column in the child table that connects it back to the parent.

    By default this is populated by converting the model class name from TitleCase to snake_case and appending _id.
    So, if the model class is called `ProductCategory`, this becomes `product_category_id`.

    This MUST correspond to the actual name of a column in the child table.
    """
    foreign_column_name = configs.ModelToIdColumn()

    """ Columns from the child table that should be included when converting this column to JSON. """
    readable_child_columns = configs.ReadableModelColumns("child_model_class")

    """ Additional queries to add to searches on the child table. """
    where = configs.Conditions()

    """ The name of the id column in the model class we belong to (automatically set) """
    parent_id_column_name = configs.ModelColumn()

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        child_model_class,
        foreign_column_name: Optional[str] = None,
        readable_child_columns: Optional[List[str]] = []
        validators: Union[Callable, Validator, BindingValidator, List[Union[Callable, Action, BindingAction]]] = [],
        is_readable: bool = True,
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
