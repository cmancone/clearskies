from __future__ import annotations
from typing import Any, Callable, overload, Self, TYPE_CHECKING, Type
from collections import OrderedDict

import clearskies.typing
import clearskies.parameters_to_properties
from clearskies import configs
from clearskies.column import Column
from clearskies.functional import string
from clearskies.autodoc.schema import Array as AutoDocArray
from clearskies.autodoc.schema import Object as AutoDocObject
from clearskies.columns.many_to_many_ids import ManyToManyIds

if TYPE_CHECKING:
    from clearskies import Model

class ManyToManyModels(Column):
    """
    A companion for the ManyToManyIds column that returns the matching models instead of the ids.

    See the example in the ManyToManyIds column to understand how to use it.
    """

    """ The name of the many-to-many column we are attached to. """
    many_to_many_column_name = configs.ModelColumn(required=True)

    is_writeable = configs.Boolean(default=False)
    is_searchable = configs.Boolean(default=False)
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
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
            raise ValueError(f"Error with configuration for {model_class.__name__}.{name}, which is a ManyToManyModels column.  It needs to point to a ManyToManyIds column, and it was told to use {model_class.__name__}.{self.many_to_many_column_name}, but this is not a ManyToManyIds column.")

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
    def __get__(self, instance: None, cls: Type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: Type[Model]) -> Model:
        pass

    def __get__(self, instance, cls):
        if instance is None:
            self.model_class = cls
            return self
        return self.many_to_many_column.get_related_models(instance)

    def __set__(self, instance, value: Model | list[Model] | list[dict[str, Any]]) -> None:
        # we allow a list of models or a model, but if it's a model it may represent a single record or a query.
        # if it's a single record then we want to wrap it in a list so we can iterate over it.
        if hasattr(value, "_data") and value._data:
            value = []
        many_to_many_column: ManyToManyIds = self.many_to_many_column # type: ignore
        related_model_class = many_to_many_column.related_model_class
        related_id_column_name = related_model_class.id_column_name
        record_ids = []
        for (index, record) in enumerate(value):
            if isinstance(record, dict):
                if not record.get(related_id_column_name):
                    raise KeyError(f"A list of dictionaries was set to '{self.model_class.__name__}.{self.name}', in which case each dictionary should contain the key '{related_id_column_name}', which should be the id of an entry for the '{related_model_class.__name__}' model.  However, no such key was found for entry #{index+1}")
                record_ids.append(record[related_id_column_name])
                continue

            # if we get here then the entry should be a model for our related model class
            if not isinstance(record, related_model_class):
                raise TypeError(f"Models were sent to '{self.model_class.__name__}.{self.name}', in which case it should be a list of models of type {related_model_class.__name__}.  However, an object of type '{record.__class__.__name__}' was found for entry #{index+1}")
            record_ids.append(getattr(record, related_id_column_name))
        setattr(instance, self.many_to_many_column_name, record_ids)

    def add_search(
        self,
        model: Model,
        value: str,
        operator: str="",
        relationship_reference: str=""
    ) -> Model:
        return self.many_to_many_column.add_search(model, value, operator, relationship_reference=relationship_reference) # type: ignore

    def to_json(self, model: Model) -> dict[str, Any]:
        records = []
        many_to_many_column: ManyToManyIds = self.many_to_many_column # type: ignore
        columns = many_to_many_column.related_columns
        related_id_column_name = many_to_many_column.related_model_class.id_column_name
        for related in many_to_many_column.get_related_models(model):
            json = OrderedDict()
            if related_id_column_name not in many_to_many_column.readable_related_column_names:
                json[related_id_column_name] = columns[related_id_column_name].to_json(related)
            for column_name in many_to_many_column.readable_related_column_names:
                column_data = columns[column_name].to_json(related)
                if type(column_data) == dict:
                    json = {**json, **column_data} # type: ignore
                else:
                    json[column_name] = column_data
            records.append(json)
        return {self.name: records}

    def documentation(self, name: str | None=None, example: str | None=None, value: str | None=None):
        many_to_many_column = self.many_to_many_column # type: ignore
        columns = many_to_many_column.related_columns
        related_id_column_name = many_to_many_column.related_model_class.id_column_name
        related_properties = [columns[related_id_column_name].documentation()]

        for column_name in many_to_many_column.readable_related_column_names:
            related_docs = columns[column_name].documentation()
            if type(related_docs) != list:
                related_docs = [related_docs]
            related_properties.extend(related_docs)

        related_object = AutoDocObject(
            string.title_case_to_nice(many_to_many_column.related_model_class.__name__),
            related_properties,
        )
        return AutoDocArray(name if name is not None else self.name, related_object, value=value)
