from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable, Self, overload

import clearskies.typing
from clearskies import configs, parameters_to_properties  # type: ignore
from clearskies.autodoc.schema import Array as AutoDocArray
from clearskies.autodoc.schema import Object as AutoDocObject
from clearskies.column import Column
from clearskies.columns.many_to_many_ids import ManyToManyIds
from clearskies.functional import string

if TYPE_CHECKING:
    from clearskies import Model


class ManyToManyPivots(Column):
    """
    A companion for the ManyToManyIds column that returns the matching pivot models instead of the ids.

    See ManyToManyIdsWithData for an example of how to use it (but note that it works just the same for the
    ManyToManyIds column).
    """

    """ The name of the many-to-many column we are attached to. """
    many_to_many_column_name = configs.ModelColumn(required=True)

    is_writeable = configs.Boolean(default=False)
    is_searchable = configs.Boolean(default=False)
    _descriptor_config_map = None

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        many_to_many_column_name,
    ):
        pass

    def finalize_configuration(self, model_class: type, name: str) -> None:
        """
        Finalize and check the configuration.
        """
        getattr(self.__class__, "many_to_many_column_name").set_model_class(model_class)
        self.model_class = model_class
        self.name = name
        self.finalize_and_validate_configuration()

        # finally, make sure we're really pointed at a many-to-many column
        many_to_many_column = getattr(model_class, self.many_to_many_column_name)
        if not isinstance(many_to_many_column, ManyToManyIds):
            raise ValueError(
                f"Error with configuration for {model_class.__name__}.{name}, which is a ManyToManyModels column.  It needs to point to a ManyToManyIds column, and it was told to use {model_class.__name__}.{self.many_to_many_column_name}, but this is not a ManyToManyIds column."
            )

    @property
    def pivot_model(self):
        return self.di.build(self.pivot_model_class, cache=True)

    @property
    def related_models(self):
        return self.di.build(self.related_model_class, cache=True)

    @property
    def related_columns(self):
        return self.related_models.get_columns()

    @property
    def many_to_many_column(self) -> ManyToManyIds:
        return getattr(self.model_class, self.many_to_many_column_name)

    @overload
    def __get__(self, instance: None, cls: type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type[Model]) -> Model:
        pass

    def __get__(self, instance, cls):
        if instance is None:
            self.model_class = cls
            return self

        many_to_many_column = self.many_to_many_column  # type: ignore
        own_column_name_in_pivot = self.config("own_column_name_in_pivot")
        my_id = data[self.config("own_id_column_name")]
        return [model for model in self.pivot_models.where(f"{own_column_name_in_pivot}={my_id}")]

    def __set__(self, instance, value: Model | list[Model] | list[dict[str, Any]]) -> None:
        raise NotImplementedError("Saving not supported for ManyToManyPivots")

    def add_search(self, model: Model, value: str, operator: str = "", relationship_reference: str = "") -> Model:
        raise NotImplementedError("Searching not supported for ManyToManyPivots")

    def to_json(self, model: Model) -> dict[str, Any]:
        records = []
        many_to_many_column = self.many_to_many_column  # type: ignore
        columns = many_to_many_column.pivot_columns
        readable_column_names = many_to_many_column.readable_pivot_column_names
        pivot_id_column_name = many_to_many_column.pivot_model_class.id_column_name
        for pivot in many_to_many_column.get_pivot_models(model):
            json = OrderedDict()
            if pivot_id_column_name not in readable_column_names:
                json[pivot_id_column_name] = columns[pivot_id_column_name].to_json(pivot)
            for column_name in readable_column_names:
                column_data = columns[column_name].to_json(pivot)
                if type(column_data) == dict:
                    json = {**json, **column_data}  # type: ignore
                else:
                    json[column_name] = column_data
            records.append(json)
        return {self.name: records}

    def documentation(self, name: str | None = None, example: str | None = None, value: str | None = None):
        many_to_many_column = self.many_to_many_column  # type: ignore
        columns = many_to_many_column.pivot_columns
        pivot_id_column_name = many_to_many_column.pivot_model_class.id_column_name
        pivot_properties = [columns[pivot_id_column_name].documentation()]

        for column_name in many_to_many_column.readable_pivot_column_names:
            pivot_docs = columns[column_name].documentation()
            if type(pivot_docs) != list:
                pivot_docs = [pivot_docs]
            pivot_properties.extend(pivot_docs)

        pivot_object = AutoDocObject(
            string.title_case_to_nice(many_to_many_column.pivot_model_class.__name__),
            pivot_properties,
        )
        return AutoDocArray(name if name is not None else self.name, pivot_object, value=value)
