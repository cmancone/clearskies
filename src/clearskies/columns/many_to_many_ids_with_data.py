from __future__ import annotations
from typing import Any, Callable, overload, Self, TYPE_CHECKING

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.columns.many_to_many_ids import ManyToManyIds

if TYPE_CHECKING:
    from clearskies import Model

class ManyToManyIdsWithData(ManyToManyIds):
    """
    A column to represent a many-to-many relationship with information stored in the relationship itself.

    This is an extention of the many-to-many column, but with one important addition: data about the
    relationship itself is stored in the pivot table.  This creates some differences, which are best
    explained by starting with an example.  Note that, like the equivalent example from the ManyToMany
    column, python compilation rules won't allow you to put all these classes in one file:

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
        thingy_id = clearskies.columns.BelongsToId(ThingyReference)
        thingt = clearskies.columns.BelongsToModel("thigie_id")
        widget_id = clearskies.columns.BelongsToId(WidgetReference)
        widget = clearskies.columns.BelongsToModel("widget_id")
        some_info = clearskies.columns.String()

    class Widget(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies'columns.String()
        thingy_ids = clearskies.columns.ManyToManyIdsWithData(
            related_model_class=ThingyReference,
            pivot_model_class=ThingyToWidgetReference,
        )
        thingies = clearskies.columns.ManyToManyModels("thingy_ids")
        thingy_widgets = clearskies.columns.ManyToManyPivots("thingy_ids")

    class Thingy(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies'columns.String()
        some_ref = clearskies.columns.String(validators=clearskies.validators.Unique())
        widget_ids = clearskies.columns.ManyToManyIdsWithData(
            related_model_class=WidgetReference,
            pivot_model_class=ThingyToWidgetReference,
        )
        widgets = clearskies.columns.ManyToManyModels("widgets")
        thingy_widgets = clearskies.columns.ManyToManyPivots("widgets")

    def my_application(widgets, thingies):
        thing_1 = thingies.create({"name": "Thing 1", "some_ref": "ASDFER"})
        thing_2 = thingies.create({"name": "Thing 2", "some_ref": "QWERTY"})
        widget = widgets.create({
            "name": "Widget 1",
            "thingies": [
                {"thingy_id": thing_1.id, "some_info": "hey"},
                {"thingy_id": thing_2.id, "some_info": "sup"},
            ],
        })

        print([thing.name for thing in widget.thingies])
        # prints ["Thing 1", "Thing 2"]
        print([thingy_widget.some_info for thingy_widget in widget.thingy_widgets])
        # prints ["hey", "sup"]

        widget.save({
            "thingies": [
                {"some_ref": "ASDFER", "some_info": "cool"},
            ]
        })

        print([thing.name for thing in widget.thingies])
        # prints ["Thing 1"]
        print([thingy_widget.some_info for thingy_widget in widget.thingy_widgets])
        # prints ["cool"]

    ```

    As with setting ids in the ManyToMany class, any items left out will result in the relationship
    (including all its related data) being removed.  An important difference with the ManyToManyWithData
    column is the way you specify which record is being connected.  This is easy for the ManyToMany column
    because all you provide is the id from the related model.  When working with the ManyToManyWithData
    column, you provide a dictionary for each relationship (so you can provide the data that goes in the
    pivot model).  To let it know what record is being connected, you therefore explicitly provide
    the id from the related model in a dictionary key with the name of the related model id column in
    the pivot (e.g. `{"thingy_id": id}` in the first example.  However, if there are unique columns in the
    related model, you can provide those instead (e.g. the second example only provides `some_ref` in the
    dictionary.
    """

    """ The list of columns in the pivot model that can be set when saving data. """
    setable_columns = configs.WriteableModelColumns("pivot_model_class")

    """ The list of columns in the pivot model that will be included when returning records. """
    readable_pivot_columns = configs.ReadableModelColumns("pivot_model_class")

    """
    Complicated, but probably should be false.

    Sometimes you have to provide data from the related model class in your save data so that
    clearskies can find the right record.  Normally, this lookup column is not persisted to the
    pivot table, because it is assumed to only exist in the related table.  In some cases though,
    you may want it in both, in which case you can set this to true.
    """
    persist_unique_lookup_column_to_pivot_table = configs.Boolean(default=False)

    """
    A default value to set for this column.

    The default is only used when creating a record for the first time, and only if
    a value for this column has not been set.
    """
    default = configs.ListAnyDict(default=None) #  type: ignore

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.ListAnyDictOrCallable(default=None) #  type: ignore

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        related_model_class,
        pivot_model_class,
        own_column_name_in_pivot: str = "",
        related_column_name_in_pivot: str = "",
        readable_related_columns: list[str] = [],
        setable_columns: list[str] = [],
        persist_unique_lookup_column_to_pivot_table: bool = False,
        default: list[dict[str, Any]] = [],
        setable: list[dict[str, Any]] | Callable[..., list[dict[str, Any]]] = [],
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

    @overload
    def __get__(self, instance: None, parent: type) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, parent: type) -> list[Any]:
        pass

    def __get__(self, instance, parent) -> list[Any]:
        return super().__get__(instance, parent)

    def __set__(self, instance, value: list[dict[str, Any]]) -> None:
        instance._next_data[self.name] = value

    def post_save(self, data, model, id):
        # if our incoming data is not in the data array or is None, then nothing has been set and we do not want
        # to make any changes
        if self.name not in data or data[self.name] is None:
            return data

        # figure out what ids need to be created or deleted from the pivot table.
        if not model.exists:
            old_ids = set()
        else:
            old_ids = set(self.__get__(model, model.__class__))

        # this is trickier for many-to-many-with-data compared to many-to-many.  We're generally
        # expecting data[self.name] to be a list of dictionaries.  For each entry, we need to find
        # the corresponding entry in the pivot table to decide if we need to delete, create, or update.
        # However, since we have a dictionary there are a variety of ways that we can connect to
        # an entry in the related table - either related id or any unique column from the related
        # table.  Technically we might also specify a pivot id, but we're generally trying to be
        # transparent to those, so let's ignore that one.
        related_column_name_in_pivot = self.related_column_name_in_pivot
        own_column_name_in_pivot = self.own_column_name_in_pivot
        unique_related_columns = {
            column.name: column.name for column in self.related_columns.values() if column.is_unique
        }
        related_model = self.related_model
        pivot_model = self.pivot_model
        new_ids = set()
        for pivot_record in data[self.name]:
            # first we need to identify which related column this belongs to.
            related_column_id = None
            # if they provide the related column id in the pivot data then we're good
            if related_column_name_in_pivot in pivot_record:
                related_column_id = pivot_record[related_column_name_in_pivot]
            elif len(unique_related_columns):
                for pivot_column, pivot_value in pivot_record.items():
                    if pivot_column not in unique_related_columns:
                        continue
                    related = related_model.find(f"{pivot_column}={pivot_value}")
                    related_column_id = related.id
                    if related_column_id:
                        # remove this column from the data - it was used to lookup the right
                        # record, but mostly won't exist in the model, unless we've been instructed
                        # to keep it
                        if not self.config("persist_unique_lookup_column_to_pivot_table"):
                            del pivot_record[pivot_column]
                        break
            if not related_column_id:
                column_list = "'" + "', '".join(list(unique_related_columns.keys())) + "'"
                raise ValueError(
                    f"Missing data for {self.name}: Unable to match related record for a record in the many-to-many relationship: you must provide either '{related_column_name_in_pivot}' with the id column for the related table, or a value from one of the unique columns: {column_list}"
                )
            pivot_model = (
                pivot_model.where(f"{related_column_name_in_pivot}={related_column_id}")
                .where(f"{own_column_name_in_pivot}={id}")
                .first()
            )
            new_ids.add(related_column_id)
            # this will either update or create accordingly
            pivot_model.save(
                {
                    **pivot_record,
                    related_column_name_in_pivot: related_column_id,
                    own_column_name_in_pivot: id,
                }
            )

        # the above took care of isnerting and updating active records.  Now we need to delete
        # records that are no longer needed.
        to_delete = old_ids - new_ids
        if to_delete:
            for model_to_delete in pivot_model.where(
                f"{related_column_name_in_pivot} IN (" + ",".join(map(str, to_delete)) + ")"
            ):
                model_to_delete.delete()

        return data
