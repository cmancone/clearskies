from typing import Callable, List, Optional, Union


from clearskies import configs, parameters_to_properties
from clearskies.bindings import Action as BindingAction
from clearskies.actions import Action
from clearskies.bindings import Validator as BindingValidator
from clearskies.columns.validators import Validator
from clearskies.columns import BelongsTo


class CategoryTree(BelongsTo):
    tree_model_class = configs.ModelClass(required=True)
    tree_parent_id_column_name = configs.ModelColumn("tree_model_class", default="parent_id")
    tree_child_id_column_name = configs.ModelColumn("tree_model_class", default="child_id")
    tree_is_parent_column_name = configs.ModelColumn("tree_model_class", default="is_parent")
    tree_level_column_name = configs.ModelColumn("tree_model_class", default="level")
    max_iterations = configs.Integer(default=100)
    children_column_name = configs.String(default="children")
    descendants_column_name = configs.String(default="descendants")
    ancestors_column_name = configs.String(default="ancestors")
    load_relatives_strategy = configs.Select(["join", "where_in", "individual"], default="join")

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        tree_model_class,
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
        where: Optional[Union[str, Callable, List[Union[str, Callable]]]] = None,
        tree_parent_id_column_name: str = "parent_id",
        tree_child_id_column_name: str = "child_id",
        tree_is_parent_column_name: str = "is_parent",
        tree_level_column_name: str = "level",
        max_iterations: int = 100,
        children_column_name: str = "children",
        descendants_column_name: str = "descendants",
        ancestors_column_name: str = "ancestors",
        load_relatives_strategy: str = "join",
    ):
        pass

    def finalize_configuration(self, model_class) -> None:
        self.parent_model_class = model_class
        self.finalize_and_validate_configuration()
