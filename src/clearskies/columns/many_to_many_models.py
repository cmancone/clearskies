from __future__ import annotations
from typing import Any, Callable, overload, Self, TYPE_CHECKING
from collections import OrderedDict

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.column import Column
from clearskies.functional import string
from clearskies.autodoc.string import Array as AutoDocArray
from clearskies.autodoc.string import Object as AutoDocObject
from clearskies.columns.many_to_many import ManyToMany

if TYPE_CHECKING:
    from clearskies import Model

class ManyToManyModels(Column):
    """
    A companion for the ManyToMany column that returns the matching models instead of the ids
    """

    """ The name of the many-to-many column we are attached to. """
    many_to_many_column_name = configs.ModelColumn(required=True)

    is_writeable = configs.Boolean(default=False)
    is_searchable = configs.Boolean(default=False)

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

    @property
    def pivot_model(self):
        return self.di.build(self.pivot_model_class, cache=True)

    @property
    def related_models(self):
        return self.di.build(self.related_model_class, cache=True)

    @property
    def related_columns(self):
        return self.related_models.get_columns()

    @overload
    def __get__(self, instance: None, parent: type) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, parent: type) -> Model:
        pass

    def __get__(self, instance, parent) -> list[str | int]:
        return self.get_related_models()

    @property
    def many_to_many_column(self) -> ManyToMany:
        return getattr(self.model_class, self.many_to_many_column_name)

    def __set__(self, instance, value: Model | list[Model] | list[dict[str, Any]) -> None:
        # we allow a list of models or a model, but if it's a model it may represent a single record or a query.
        # if it's a single record then we want to wrap it in a list so we can iterate over it.
        if hasattr(value, "_data") and value._data:
            value = []
        related_model_class = self.many_to_many_column.related_model_class
        related_id_column_name = related_model_class.id_column_name
        record_ids = []
        for (index, record) in enumerate(value):
            if isinstance(record, dict):
                if not record.get(related_id_column_name):
                    raise KeyError(f"A list of dictionaries was set to '{self.model_class.__name__}.{self.name}', in which case each dictionary should contain the key '{related_id_column_name}', which should be the id of an entry for the '{related_model_class.__name__}' model.  However, no such key was found for entry #{index+1}")
                records_ids.append(record[related_id_column_name])
                continue

            # if we get here then the entry should be a model for our related model class
            if not isinstance(record, related_model_class):
                raise TypeError(f"Models were sent to '{self.model_class.__name__}.{self.name}', in which case it should be a list of models of type {related_model_class.__name__}.  However, an object of type '{record.__class__.__name__}' was found for entry #{index+1}")
            record_ids.append(getattr(record, related_id_column_name))
        setattr(model, self.many_to_many_column_name, record_ids)

    def add_search(
        self,
        model: Model,
        value: str,
        operator: str="",
        relationship_reference: str=""
    ) -> Model:
        return self.many_to_many_column.add_search(model, value, operator, relationship_reference=relationship_reference)

    def to_json(self, model: Model) -> dict[str, Any]:
        records = []
        many_to_many_column = self.many_to_many_column
        columns = many_to_many_column.related_columns
        related_id_column_name = many_to_many_column.related_model_class.id_column_name
        for related in many_to_many_column.get_related_models():
            json = OrderedDict()
            if related_id_column_name not in many_to_many_column.readable_related_columns:
                json[related_id_column_name] = columns[related_id_column_name].to_json(related)
            for column_name in many_to_many_column.readable_related_columns:
                column_data = columns[column_name].to_json(related)
                if type(column_data) == dict:
                    json = {**json, **column_data}
                else:
                    json[column_name] = column_data
            records.append(json)
        return {self.name: records}

    def documentation(self, name: str | None=None, example: str | None=None, value: str | None=None):
        many_to_many_column = self.many_to_many_column
        columns = many_to_many_column.related_columns
        related_id_column_name = many_to_many_column.related_model_class.id_column_name
        related_properties = [columns[related_id_column_name].documentation()]

        for column_name in many_to_many_column.readable_related_columns:
            related_docs = columns[column_name].documentation()
            if type(related_docs) != list:
                related_docs = [related_docs]
            related_properties.extend(related_docs)

        related_object = AutoDocObject(
            string.title_case_to_nice(many_to_many_column.related_model_class.__name__),
            related_properties,
        )
        return AutoDocArray(name if name is not None else self.name, related_object, value=value)
