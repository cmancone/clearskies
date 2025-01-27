from __future__ import annotations
from typing import Any, Callable, overload, Self, TYPE_CHECKING, Type
from collections import OrderedDict

import clearskies.typing
import clearskies.parameters_to_properties
from clearskies import configs
from clearskies.column import Column
from clearskies.functional import string
from clearskies.autodoc.schema import Array as AutoDocArray
from clearskies.autodoc.schema import String as AutoDocString

if TYPE_CHECKING:
    from clearskies import Column
    from clearskies import Model

class ManyToManyIds(Column):
    """
    A column to represent a many-to-many relationship.

    This is different from belongs to/has many because with those, every child has only one parent.  With a many-to-many
    relationship, both models can have multiple relatives from the other model.  In order to support this, it's necessary
    to have a third model (the pivot model) that records the relationships.  In general this table just needs three
    columns: it's own id, and then one column for each other model to store the id of the related records.
    You can specify the names of these columns but it also follows the standard naming convention by default:
    take the class name, convert it to snake case, and append `_id`.

    Note, there is a variation on this (`ManyToManyIdsWithData`) where additional data is stored in the pivot table
    to record information about the relationship.

    This column is writeable.  You would set it to a list of ids from the related model that denotes which
    records it is related to.

    The following example shows usage.  It relies on model references to avoid circular imports.  Also note
    that each model class would have to go in a separate file.  You can't actually dump this all in one file
    because all the models reference eachother - Python will complain about references to classes that don't
    exist.

    ```
    import clearskies

    class WidgetReference:
        def get_model_class(self):
            return widget.Widget

    class ThingyReference:
        def get_model_class(self):
            return thingy.Thingy

    class ThingyToWidgetReference:
        def get_model_class(self):
            return thingy_to_widget.ThingyToWidget

    class ThingyToWidget(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        # these could also be belongs to relationships, but the pivot model
        # is rarely used directly, so it may not matter
        thingy_id = clearskies.columns.Uuid()
        widget_id = clearskies.columns.Uuid()

    class Widget(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies'columns.String()
        thingy_ids = clearskies.columns.ManyToManyIds(
            related_model_class=ThingyReference,
            pivot_model_class=ThingyToWidgetReference,
        )
        thingies = clearskies.columns.ManyToManyModels("thingy_ids")

    class Thingy(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies'columns.String()
        widget_ids = clearskies.columns.ManyToManyIds(
            related_model_class=WidgetReference,
            pivot_model_class=ThingyToWidgetReference,
        )
        widgets = clearskies.columns.ManyToManyModels("widget_ids")

    def my_application(widgets, thingies):
        thing_1 = thingies.create({"name": "Thing 1"})
        thing_2 = thingies.create({"name": "Thing 2"})
        widget = widgets.create({
            "name": "Widget 1",
            "thingy_ids": [thing_1.id, thing_2.id],
        })

        print([thing.name for thing in widget.thingies])
        # prints ["Thing 1", "Thing 2"]
        print(widget.thingy_ids)
        # The equivalent of [thing.id for thing in widget.thingies]

        widget.save({
            "thingies": [thing_2.id],
        })

        print([thing.name for thing in widget.thingies])
        # prints ["Thing 2"]

    Whatever list of ids you save to the column will become the new list of related records.
    You can use the ids reference column to get the current list of ids and add or remove items as needed:

    ```
    widget.save({
        "thingy_ids": [...widget.thingy_ids, some_other_id],
    })

    widget.save({
        "thingy_ids": [id for id in widget.thingy_ids if id != "some_id_to_remove"]
    })
    ```

    and of course you can also create or remove individual relationships by using the pivot model:

    ```
    def add_items(thingy_to_widgets):
        thingy_to_widgets.create({
            "thingy_id": "some_id",
            "widget_id": "other_id",
        })

    def remove_item(thingy_to_widgets):
        thingy_to_widgets.where("thingy_id=some_id").where("widget_id=other_id").first().delete()
    ```

    """

    """ The model class for the model that we are related to. """
    related_model_class = configs.ModelClass(required=True)

    """ The model class for the pivot table - the table used to record connections between ourselves and our related table. """
    pivot_model_class = configs.ModelClass(required=True)

    """ The name of the column in the pivot table (the column that contains the id of records from our table). """
    own_column_name_in_pivot = configs.ModelToIdColumn()

    """ The name of the column in the pivot table that contains the id of records from the related table. """
    related_column_name_in_pivot = configs.ModelToIdColumn("related_model_class")

    """ The name of the pivot table (loaded automatically). """
    pivot_table = configs.ModelDestinationName("pivot_model_class")

    """ The list of columns to be loaded from the related models when we are converted to JSON. """
    readable_related_columns = configs.ReadableModelColumns("related_model_class")

    """
    A default value to set for this column.

    The default is only used when creating a record for the first time, and only if
    a value for this column has not been set.
    """
    default = configs.StringList(default=None) #  type: ignore

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.StringListOrCallable(default=None) #  type: ignore

    is_searchable = configs.Boolean(default=False)

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        related_model_class,
        pivot_model_class,
        own_column_name_in_pivot: str = "",
        related_column_name_in_pivot: str = "",
        readable_related_columns: list[str] = [],
        default: list[str] = [],
        setable: list[str] | Callable[..., list[str]] = [],
        is_readable: bool = True,
        is_writeable: bool = True,
        is_temporary: bool = False,
        validators: clearskies.typing.validator | list[clearskies.typing.validator] = [],
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
        created_by_source_strict: bool = True,
    ):
        pass

    def to_backend(self, data):
        # we can't persist our mapping data to the database directly, so remove anything here
        # and take care of things in post_save
        if self.name in data:
            del data[self.name]
        return data

    @property
    def pivot_model(self) -> Model:
        return self.di.build(self.pivot_model_class, cache=True)

    @property
    def related_model(self) -> Model:
        return self.di.build(self.related_model_class, cache=True)

    @property
    def related_columns(self) -> dict[str, Column]:
        return self.related_model.get_columns()

    @property
    def pivot_columns(self) -> dict[str, Column]:
        return self.pivot_model.get_columns()

    @overload
    def __get__(self, instance: None, parent: Type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, parent: Type[Model]) -> list[str | int]:
        pass

    def __get__(self, instance, parent):
        related_id_column_name = self.related_model_class.id_column_name
        return [getattr(model, related_id_column_name) for model in self.get_related_models(model)]

    def __set__(self, instance, value: list[str | int]) -> None:
        instance._next_data[self.name] = value

    def get_related_models(self, model: Model) -> Model:
        related_column_name_in_pivot = self.related_column_name_in_pivot
        own_column_name_in_pivot = self.own_column_name_in_pivot
        pivot_table = self.pivot_table
        related_id_column_name = self.related_model_class.id_column_name
        model_id = getattr(model, self.model_class.id_column_name)
        model = self.related_model
        join = f"JOIN {pivot_table} ON {pivot_table}.{related_column_name_in_pivot}={model.destination_name()}.{related_id_column_name}"
        related_models = model.join(join).where(f"{pivot_table}.{own_column_name_in_pivot}={model_id}")
        return related_models

    def get_pivot_models(self, model: Model) -> Model:
        return self.pivot_model.where(f"{self.own_column_name_in_pivot}=" + getattr(model, self.model_class.id_column_name))

    def post_save(self, data: dict[str, Any], model: clearskies.model.Model, id: int | str) -> None:
        # if our incoming data is not in the data array or is None, then nothing has been set and we do not want
        # to make any changes
        if self.name not in data or data[self.name] is None:
            return

        # figure out what ids need to be created or deleted from the pivot table.
        if not model:
            old_ids = set()
        else:
            old_ids = set(self.__get__(model, model.__class__))

        new_ids = set(data[self.name])
        to_delete = old_ids - new_ids
        to_create = new_ids - old_ids
        pivot_model = self.pivot_model
        related_column_name_in_pivot = self.related_column_name_in_pivot
        if to_delete:
            for model_to_delete in pivot_model.where(
                f"{related_column_name_in_pivot} IN ({','.join(map(str, to_delete))})"
            ):
                model_to_delete.delete()
        if to_create:
            own_column_name_in_pivot = self.own_column_name_in_pivot
            for id_to_create in to_create:
                pivot_model.create(
                    {
                        related_column_name_in_pivot: id_to_create,
                        own_column_name_in_pivot: id,
                    }
                )

        super().post_save(data, model, id)

    def add_search(
        self,
        model: Model,
        value: str,
        operator: str="",
        relationship_reference: str=""
    ) -> Model:
        related_column_name_in_pivot = self.related_column_name_in_pivot
        own_column_name_in_pivot = self.own_column_name_in_pivot
        own_id_column_name = self.model_class.id_column_name
        pivot_table = self.pivot_table
        my_table_name = self.model_class.destination_name()
        related_table_name = self.related_model.destination_name()
        join_pivot = (
            f"JOIN {pivot_table} ON {pivot_table}.{own_column_name_in_pivot}={my_table_name}.{own_id_column_name}"
        )
        # no reason we can't support searching by both an id or a list of ids
        values = value if type(value) == list else [value]
        search = " IN (" + ", ".join([str(val) for val in value]) + ")"
        return model.join(join_pivot).where(f"{pivot_table}.{related_column_name_in_pivot}{search}")

    def to_json(self, model: Model) -> dict[str, Any]:
        related_id_column_name = self.related_model_class.id_column_name
        records = [getattr(related, related_id_column_name) for related in self.get_related_models(model)]
        return {self.name: records}

    def documentation(self, name: str | None=None, example: str | None=None, value: str | None=None):
        related_id_column_name = self.related_model_class.id_column_name
        return AutoDocArray(name if name is not None else self.name, AutoDocString(related_id_column_name))
