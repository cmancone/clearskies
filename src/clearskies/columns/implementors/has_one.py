from .has_many import HasMany
import re
from collections import OrderedDict
from ..autodoc.schema import Array as AutoDocArray
from ..autodoc.schema import Object as AutoDocObject
from ..autodoc.schema import String as AutoDocString


class HasOne(HasMany):
    """
    Controls a has-one relationship.

    This is a readonly column.  When used in a model context it will return the related record.
    When used in an API context, it will convert the child record into an object.

    It assumes that the foreign id in the child table is `[parent_model_class_name]_id` in all lower case.
    e.g., if the parent model class is named Status, then it assumes an id in the child class called `status_id`.
    """

    def can_provide(self, column_name):
        return column_name == self.name

    def provide(self, data, column_name):
        foreign_column_name = self.config("foreign_column_name")
        id_column_name = self.config("parent_id_column_name")
        return self.child_models.find(f"{foreign_column_name}={data[id_column_name]}")

    def to_json(self, model):
        json = OrderedDict()
        columns = self.get_child_columns()
        child = model.__getattr__(self.name)
        child_id_column_name = child.id_column_name
        json = {
            **json,
            **columns[child_id_column_name].to_json(child),
        }
        for column_name in self.config("readable_child_columns"):
            json = {
                **json,
                **columns[column_name].to_json(child),
            }
        return {self.name: json}

    def documentation(self, name=None, example=None, value=None):
        columns = self.get_child_columns()
        child_id_column_name = self.child_models.get_id_column_name()
        child_properties = [columns[child_id_column_name].documentation()]

        for column_name in self.config("readable_child_columns"):
            child_docs = columns[column_name].documentation()
            if type(child_docs) != list:
                child_docs = [child_docs]
            child_properties.extend(child_docs)

        return AutoDocObject(
            self.camel_to_nice(self.child_models.model_class().__name__),
            child_properties,
        )
