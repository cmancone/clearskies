from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Self, overload

import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.columns.many_to_many_ids import ManyToManyIds

if TYPE_CHECKING:
    from clearskies import Model


class ManyToManyIdsWithData(ManyToManyIds):
    """
    A column to represent a many-to-many relationship with information stored in the relationship itself.

    This is an extention of the many-to-many column, but with one important addition: data about the
    relationship is stored in the pivot table.  This creates some differences, which are best
    explained by example:

    ```
    import clearskies


    class ThingyWidgets(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        # these could also be belongs to relationships, but the pivot model
        # is rarely used directly, so I'm being lazy to avoid having to use
        # model references.
        thingy_id = clearskies.columns.String()
        widget_id = clearskies.columns.String()
        name = clearskies.columns.String()
        kind = clearskies.columns.String()


    class Thingy(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()


    class Widget(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        thingy_ids = clearskies.columns.ManyToManyIdsWithData(
            related_model_class=Thingy,
            pivot_model_class=ThingyWidgets,
            readable_pivot_column_names=["id", "thingy_id", "widget_id", "name", "kind"],
        )
        thingies = clearskies.columns.ManyToManyModels("thingy_ids")
        thingy_widgets = clearskies.columns.ManyToManyPivots("thingy_ids")


    def my_application(widgets: Widget, thingies: Thingy):
        thing_1 = thingies.create({"name": "Thing 1"})
        thing_2 = thingies.create({"name": "Thing 2"})
        thing_3 = thingies.create({"name": "Thing 3"})
        widget = widgets.create({
            "name": "Widget 1",
            "thingy_ids": [
                {"thingy_id": thing_1.id, "name": "Widget Thing 1", "kind": "Special"},
                {"thingy_id": thing_2.id, "name": "Widget Thing 2", "kind": "Also Special"},
            ],
        })

        return widget


    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(
            my_application,
            model_class=Widget,
            return_records=True,
            readable_column_names=["id", "name", "thingy_widgets"],
        ),
        classes=[Widget, Thingy, ThingyWidgets],
    )

    if __name__ == "__main__":
        cli()
    ```

    As with setting ids in the ManyToManyIds class, any items left out will result in the relationship
    (including all its related data) being removed.  An important difference with the ManyToManyWithData
    column is the way you specify which record is being connected.  This is easy for the ManyToManyIds column
    because all you provide is the id from the related model.  When working with the ManyToManyWithData
    column, you provide a dictionary for each relationship (so you can provide the data that goes in the
    pivot model).  To let it know what record is being connected, you therefore explicitly provide
    the id from the related model in a dictionary key with the name of the related model id column in
    the pivot (e.g. `{"thingy_id": id}` in the first example.  However, if there are unique columns in the
    related model, you can provide those instead.  If you execute the above example you'll get:

    ```
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "c4be91a8-85a1-4e29-994a-327f59e26ec7",
            "name": "Widget 1",
            "thingy_widgets": [
                {
                    "id": "3a8f6f14-9657-49d8-8844-0db3452525fe",
                    "thingy_id": "db292ebc-7b2b-4306-aced-8e6d073ec264",
                    "widget_id": "c4be91a8-85a1-4e29-994a-327f59e26ec7",
                    "name": "Widget Thing 1",
                    "kind": "Special",
                },
                {
                    "id": "480a0192-70d9-4363-a669-4a59f0b56730",
                    "thingy_id": "d469dbe9-556e-46f3-bc48-03f8cb8d8e44",
                    "widget_id": "c4be91a8-85a1-4e29-994a-327f59e26ec7",
                    "name": "Widget Thing 2",
                    "kind": "Also Special",
                },
            ],
        },
        "pagination": {},
        "input_errors": {},
    }
    ```
    """

    """ The list of columns in the pivot model that can be set when saving data from an endpoint. """
    setable_column_names = configs.WriteableModelColumns("pivot_model_class")

    """ The list of columns in the pivot model that will be included when returning records from an endpoint. """
    readable_pivot_column_names = configs.ReadableModelColumns("pivot_model_class")

    """
    Complicated, but probably should be false.

    Sometimes you have to provide data from the related model class in your save data so that
    clearskies can find the right record.  Normally, this lookup column is not persisted to the
    pivot table, because it is assumed to only exist in the related table.  In some cases though,
    you may want it in both, in which case you can set this to true.
    """
    persist_unique_lookup_column_to_pivot_table = configs.Boolean(default=False)

    default = configs.ListAnyDict(default=None)  #  type: ignore
    setable = configs.ListAnyDictOrCallable(default=None)  #  type: ignore
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        related_model_class,
        pivot_model_class,
        own_column_name_in_pivot: str = "",
        related_column_name_in_pivot: str = "",
        readable_related_columns: list[str] = [],
        readable_pivot_column_names: list[str] = [],
        setable_column_names: list[str] = [],
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
    def __get__(self, instance: None, cls: type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type[Model]) -> list[Any]:
        pass

    def __get__(self, instance, cls):
        return super().__get__(instance, cls)

    def __set__(self, instance, value: list[dict[str, Any]]) -> None:  # type: ignore
        instance._next_data[self.name] = value

    def post_save(self, data, model, id):
        # if our incoming data is not in the data array or is None, then nothing has been set and we do not want
        # to make any changes
        if self.name not in data or data[self.name] is None:
            return data

        # figure out what ids need to be created or deleted from the pivot table.
        if not model:
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
        # minor cheating
        if hasattr(pivot_model.backend, "create_table"):
            pivot_model.backend.create_table(pivot_model)
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
            pivot = (
                pivot_model.where(f"{related_column_name_in_pivot}={related_column_id}")
                .where(f"{own_column_name_in_pivot}={id}")
                .first()
            )
            new_ids.add(related_column_id)
            # this will either update or create accordingly
            pivot.save(
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
