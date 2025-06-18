from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable, Self, overload

import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.autodoc.schema import Array as AutoDocArray
from clearskies.autodoc.schema import String as AutoDocString
from clearskies.column import Column
from clearskies.functional import string

if TYPE_CHECKING:
    from clearskies import Column, Model

class ManyToManyIds(Column):
    """
    A column that represents a many-to-many relationship.

    This is different from belongs to/has many because with those, every child has only one parent.  With a many-to-many
    relationship, both models can have multiple relatives from the other model class.  In order to support this, it's necessary
    to have a third model (the pivot model) that records the relationships.  In general this table just needs three
    columns: it's own id, and then one column for each other model to store the id of the related records.
    You can specify the names of these columns but it also follows the standard naming convention by default:
    take the class name, convert it to snake case, and append `_id`.

    Note, there is a variation on this (`ManyToManyIdsWithData`) where additional data is stored in the pivot table
    to record information about the relationship.

    This column is writeable.  You would set it to a list of ids from the related model that denotes which
    records it is related to.

    The following example shows usage.  Normally the many-to-many column exists for both related models, but in this
    specific example it only exists for one of the models.  This is done so that the example can fit in a single file
    and therefore be easy to demonstrate.  In order to have both models reference eachother, you have to use model
    references to avoid circular imports.  There are examples of doing this in the `BelongsTo` column class.

    ```
    import clearskies

    class ThingyToWidget(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        # these could also be belongs to relationships, but the pivot model
        # is rarely used directly, so I'm being lazy to avoid having to use
        # model references.
        thingy_id = clearskies.columns.String()
        widget_id = clearskies.columns.String()

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
        thingy_ids = clearskies.columns.ManyToManyIds(
            related_model_class=Thingy,
            pivot_model_class=ThingyToWidget,
        )
        thingies = clearskies.columns.ManyToManyModels("thingy_ids")


    def my_application(widgets: Widget, thingies: Thingy):
        thing_1 = thingies.create({"name": "Thing 1"})
        thing_2 = thingies.create({"name": "Thing 2"})
        thing_3 = thingies.create({"name": "Thing 3"})
        widget = widgets.create({
            "name": "Widget 1",
            "thingy_ids": [thing_1.id, thing_2.id],
        })

        # remove an item by saving without it's id in place
        widget.save({"thingy_ids": [thing.id for thing in widget.thingies if thing.id != thing_1.id]})

        # add an item by saving and adding the new id
        widget.save({"thingy_ids": [*widget.thingy_ids, thing_3.id]})

        return widget.thingies

    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(
            my_application,
            model_class=Thingy,
            return_records=True,
            readable_column_names=["id", "name"],
        ),
        classes=[Widget, Thingy, ThingyToWidget],
    )

    if __name__ == "__main__":
        cli()
    ```

    And when executed:

    ```
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "741bc838-c694-4624-9fc2-e9032f6cb962",
                "name": "Thing 2"
            },
            {
                "id": "1808a8ef-e288-44e6-9fed-46e3b0df057f",
                "name": "Thing 3"
            }
        ],
        "pagination": {},
        "input_errors": {}
    }
    ```

    Of course, you can also create or remove individual relationships by using the pivot model directly,
    as shown in these partial code snippets:

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

    """
    The name of the column in the pivot table that contains the id of records from the model with this column.

    A default name is created by taking the model class name, converting it to snake case, and then appending `_id`.
    If you name your columns according to this standard then you don't have to specify this column name.
    """
    own_column_name_in_pivot = configs.ModelToIdColumn(model_column_config_name="pivot_model_class")

    """
    The name of the column in the pivot table that contains the id of records from the related table.

    A default name is created by taking the name of the related model class, converting it to snake case, and then
    appending `_id`. If you name your columns according to this standard then you don't have to specify this column
    name.
    """
    related_column_name_in_pivot = configs.ModelToIdColumn(model_column_config_name="pivot_model_class", source_model_class_config_name="related_model_class")

    """ The name of the pivot table."""
    pivot_table_name = configs.ModelDestinationName("pivot_model_class")

    """ The list of columns to be loaded from the related models when we are converted to JSON. """
    readable_related_column_names = configs.ReadableModelColumns("related_model_class")

    default = configs.StringList(default=None) #  type: ignore
    setable = configs.StringListOrCallable(default=None) #  type: ignore
    is_searchable = configs.Boolean(default=False)
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        related_model_class,
        pivot_model_class,
        own_column_name_in_pivot: str = "",
        related_column_name_in_pivot: str = "",
        readable_related_column_names: list[str] = [],
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

    def finalize_configuration(self, model_class: type, name: str) -> None:
        """
        Finalize and check the configuration.

        This is an external trigger called by the model class when the model class is ready.
        The reason it exists here instead of in the constructor is because some columns are tightly
        connected to the model class, and can't validate configuration until they know what the model is.
        Therefore, we need the model involved, and the only way for a property to know what class it is
        in is if the parent class checks in (which is what happens here).
        """
        self.model_class = model_class
        self.name = name
        getattr(self.__class__, "pivot_table_name").finalize_and_validate_configuration(self)
        own_column_name_in_pivot_config = getattr(self.__class__, "own_column_name_in_pivot")
        own_column_name_in_pivot_config.source_model_class = model_class
        own_column_name_in_pivot_config.finalize_and_validate_configuration(self)
        self.finalize_and_validate_configuration()

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
    def __get__(self, instance: None, cls: type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type[Model]) -> list[str | int]:
        pass

    def __get__(self, instance, cls):
        if instance is None:
            self.model_class = cls
            return self
        related_id_column_name = self.related_model_class.id_column_name
        return [getattr(model, related_id_column_name) for model in self.get_related_models(instance)]

    def __set__(self, instance, value: list[str | int]) -> None:
        instance._next_data[self.name] = value

    def get_related_models(self, model: Model) -> Model:
        related_column_name_in_pivot = self.related_column_name_in_pivot
        own_column_name_in_pivot = self.own_column_name_in_pivot
        pivot_table_name = self.pivot_table_name
        related_id_column_name = self.related_model_class.id_column_name
        model_id = getattr(model, self.model_class.id_column_name)
        model = self.related_model
        join = f"JOIN {pivot_table_name} ON {pivot_table_name}.{related_column_name_in_pivot}={model.destination_name()}.{related_id_column_name}"
        related_models = model.join(join).where(f"{pivot_table_name}.{own_column_name_in_pivot}={model_id}")
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
        pivot_table_name = self.pivot_table_name
        my_table_name = self.model_class.destination_name()
        related_table_name = self.related_model.destination_name()
        join_pivot = (
            f"JOIN {pivot_table_name} ON {pivot_table_name}.{own_column_name_in_pivot}={my_table_name}.{own_id_column_name}"
        )
        # no reason we can't support searching by both an id or a list of ids
        values = value if type(value) == list else [value]
        search = " IN (" + ", ".join([str(val) for val in value]) + ")"
        return model.join(join_pivot).where(f"{pivot_table_name}.{related_column_name_in_pivot}{search}")

    def to_json(self, model: Model) -> dict[str, Any]:
        related_id_column_name = self.related_model_class.id_column_name
        records = [getattr(related, related_id_column_name) for related in self.get_related_models(model)]
        return {self.name: records}

    def documentation(self, name: str | None=None, example: str | None=None, value: str | None=None):
        related_id_column_name = self.related_model_class.id_column_name
        return AutoDocArray(name if name is not None else self.name, AutoDocString(related_id_column_name))
