from __future__ import annotations
from typing import TYPE_CHECKING, overload, Self, Type

import clearskies.parameters_to_properties
from clearskies import configs
from clearskies.column import Column
from clearskies.columns import CategoryTree

if TYPE_CHECKING:
    from clearskies import Model

class CategoryTreeChildren(Column):
    """
    Returns the child categories in a category tree relationship.
    """

    """ The name of the category tree column we are connected to. """
    category_tree_column_name = configs.ModelColumn(required=True)

    is_writeable = configs.Boolean(default=False)
    is_searchable = configs.Boolean(default=False)
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        category_tree_column_name: str,
    ):
        pass

    def finalize_configuration(self, model_class: type, name: str) -> None:
        """
        Finalize and check the configuration.
        """
        getattr(self.__class__, "category_tree_column_name").set_model_class(model_class)
        self.model_class = model_class
        self.name = name
        self.finalize_and_validate_configuration()

        # double check that we are pointed to a category tree column
        category_tree_column = getattr(model_class, self.category_tree_column_name)
        if not isinstance(category_tree_column, CategoryTree):
            raise ValueError(f"Error with configuration for {model_class.__name__}.{name}, which is a {self.__class__.__name__}.  It needs to point to a category tree column, and it was told to use {model_class.__name__}.{self.category_tree_column_name}, but this is not a CategoryTree column.")

    @overload
    def __get__(self, instance: None, cls: Type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: Type[Model]) -> Model:
        pass

    def __get__(self, model, cls):
        if model is None:
            self.model_class = cls
            return self # type:  ignore

        return self.relatives(model)

    def __set__(self, model: Model, value: Model) -> None:
        raise ValueError(f"Attempt to set a value to '{model.__class__.__name__}.{self.name}, but this column is not writeable")

    def relatives(self, model: Model, include_all: bool=False, find_parents: bool=False) -> Model | list[Model]:
        id_column_name = model.id_column_name
        model_id = getattr(model, id_column_name)
        model_table_name = model.destination_name()
        category_tree_column = getattr(self.model_class, self.category_tree_column_name)
        tree_table_name = category_tree_column.tree_model_class.destination_name()
        parent_id_column_name = category_tree_column.tree_parent_id_column_name
        child_id_column_name = category_tree_column.tree_child_id_column_name
        is_parent_column_name = category_tree_column.tree_is_parent_column_name
        level_column_name = category_tree_column.tree_level_column_name

        if find_parents:
            join_on = parent_id_column_name
            search_on = child_id_column_name
        else:
            join_on = child_id_column_name
            search_on = parent_id_column_name

        # if we can join then use a join.
        if category_tree_column.load_relatives_strategy:
            relatives = category_tree_column.parent_model.join(
                f"{tree_table_name} as tree on tree.{join_on}={model_table_name}.{id_column_name}"
            )
            relatives = relatives.where(f"tree.{search_on}={model_id}")
            if not include_all:
                relatives = relatives.where(f"tree.{is_parent_column_name}=1")
            if find_parents:
                relatives = relatives.sort_by(level_column_name, "asc")
            return relatives

        # joins only work for SQL-like backends.  Otherwise, we have to pull out our list of ids
        branches = category_tree_column.tree_model.where(f"{search_on}={model_id}")
        if not include_all:
            branches = branches.where(f"{is_parent_column_name}=1")
        if find_parents:
            branches = branches.sort_by(level_column_name, "asc")
        ids = [str(branch.get(join_on)) for branch in branches]

        # Can we search with a WHERE IN() clause?  If the backend supports it, it is probably faster
        if category_tree_column.load_relatives_strategy == "where_in":
            return category_tree_column.parent_model.where(f"{id_column_name} IN ('" + "','".join(ids) + "')")

        # otherwise we have to load each model individually which is SLOW....
        return [category_tree_column.parent_model.find(f"{id_column_name}={id}") for id in ids]
