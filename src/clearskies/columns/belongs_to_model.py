from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Self, overload

import clearskies.parameters_to_properties
from clearskies import configs
from clearskies.column import Column
from clearskies.columns.belongs_to_id import BelongsToId
from clearskies.functional import validations

if TYPE_CHECKING:
    from clearskies import Model


class BelongsToModel(Column):
    """Return the model object for a belongs to relationship."""

    """ The name of the belongs to column we are connected to. """
    belongs_to_column_name = configs.ModelColumn(required=True)

    is_temporary = clearskies.configs.boolean.Boolean(default=True)
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        belongs_to_column_name: str,
    ):
        pass

    def finalize_configuration(self, model_class: type, name: str) -> None:
        """Finalize and check the configuration."""
        getattr(self.__class__, "belongs_to_column_name").set_model_class(model_class)
        self.model_class = model_class
        self.name = name
        self.finalize_and_validate_configuration()

        # finally, let the belongs to column know about us and make sure it's the right thing.
        belongs_to_column = getattr(model_class, self.belongs_to_column_name)
        if not isinstance(belongs_to_column, BelongsToId):
            raise ValueError(
                f"Error with configuration for {model_class.__name__}.{name}, which is a BelongsToModel.  It needs to point to a belongs to column, and it was told to use {model_class.__name__}.{self.belongs_to_column_name}, but this is not a BelongsToId column."
            )
        belongs_to_column.model_column_name = name

    @overload
    def __get__(self, instance: None, cls: type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type[Model]) -> Model:
        pass

    def __get__(self, model, cls):
        if model is None:
            self.model_class = cls
            return self  # type:  ignore

        # this makes sure we're initialized
        if "name" not in self._config:
            model.get_columns()

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

    def pre_save(self, data: dict[str, Any], model: Model) -> dict[str, Any]:
        # if we have a model coming in then we want to extract the id.  Either way, the model id needs to go to the
        # belongs_to_id column, which is the only one that is actually saved.
        if self.name in data:
            value = data[self.name]
            data[self.belongs_to_column_name] = (
                getattr(value, value.id_column_name) if validations.is_model(value) else value
            )
        return super().pre_save(data, model)

    def add_join(self, model: Model) -> Model:
        return getattr(model.__class__, self.belongs_to_column_name).add_join(model)

    def join_table_alias(self) -> str:
        return getattr(self.model_class, self.belongs_to_column_name).join_table_alias()

    def add_search(
        self, model: clearskies.model.Model, value: str, operator: str = "", relationship_reference: str = ""
    ) -> clearskies.model.Model:
        return getattr(self.model_class, self.belongs_to_column_name).add_search(
            model, value, operator, relationship_reference=relationship_reference
        )

    def to_json(self, model: Model) -> dict[str, Any]:
        """Convert the column into a json-friendly representation."""
        belongs_to_column = getattr(model.__class__, self.belongs_to_column_name)
        if not belongs_to_column.readable_parent_columns:
            raise ValueError(
                f"Configuration error for {model.__class__.__name__}: I can't convert to JSON unless you set readable_parent_columns on my parent attribute, {model.__class__.__name__}.{self.belongs_to_column_name}."
            )

        # otherwise return an object with the readable parent columns
        columns = belongs_to_column.parent_columns
        parent = getattr(model, self.name)
        json: dict[str, Any] = OrderedDict()
        for column_name in belongs_to_column.readable_parent_columns:
            json = {**json, **columns[column_name].to_json(parent)}  # type: ignore
        return {
            self.name: json,
        }
