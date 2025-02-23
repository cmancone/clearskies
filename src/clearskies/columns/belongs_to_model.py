from __future__ import annotations
from typing import Type, TYPE_CHECKING, overload, Self

from clearskies import configs
from clearskies.column import Column
from clearskies.columns.belongs_to_id import BelongsToId
import clearskies.parameters_to_properties

if TYPE_CHECKING:
    from clearskies import Model

class BelongsToModel(Column):
    """
    Returns the model object for a belongs to relationship.  See the docs on the BelongsToId column for usage.
    """

    """ The name of the belongs to column we are connected to. """
    belongs_to_column_name = configs.ModelColumn(required=True)

    is_writeable = configs.Boolean(default=False)
    is_searchable = configs.Boolean(default=False)
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        belongs_to_column_name: str,
    ):
        pass

    def finalize_configuration(self, model_class: type, name: str) -> None:
        """
        Finalize and check the configuration.
        """
        getattr(self.__class__, "belongs_to_column_name").set_model_class(model_class)
        self.model_class = model_class
        self.name = name
        self.finalize_and_validate_configuration()

        # finally, let the belongs to column know about us and make sure it's the right thing.
        belongs_to_column = getattr(model_class, self.belongs_to_column_name)
        if not isinstance(belongs_to_column, BelongsToId):
            raise ValueError(f"Error with configuration for {model_class.__name__}.{name}, which is a BelongsToModel.  It needs to point to a belongs to column, and it was told to use {model_class.__name__}.{self.belongs_to_column_name}, but this is not a BelongsToId column.")
        belongs_to_column.model_column_name = name

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

        belongs_to_column = getattr(model.__class__, self.belongs_to_column_name)
        parent_id = getattr(model, self.belongs_to_column_name)
        parent_class = belongs_to_column.parent_model_class
        parent_model = self.di.build(parent_class, cache=False)
        if not parent_id:
            return parent_model.empty_model()

        parent_id_column_name = parent_model.id_column_name
        join_alias = belongs_to_column.join_table_alias()
        raw_data = model.get_raw_data()

        # sometimes the model is loaded via the N+1 functionality, in which case the data will already exist
        # in model.data but hiding under a different name.
        if raw_data.get(f"{join_alias}.{parent_id_column_name}"):
            parent_data = {parent_id_column_name: raw_data[f"{join_alias}_{parent_id_column_name}"]}
            for column_name in belongs_to_column.readable_parent_columns:
                select_alias = f"{join_alias}_{column_name}"
                parent_data[column_name] = raw_data[select_alias] if select_alias in raw_data else None
            return parent_model.model(parent_data)

        return parent_model.find(f"{parent_id_column_name}={parent_id}")

    def __set__(self, model: Model, value: Model) -> None:
        setattr(model, self.belongs_to_column_name, getattr(value, value.id_column_name))
