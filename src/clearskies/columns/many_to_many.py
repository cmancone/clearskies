from typing import Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.column import Column


class ManyToMany(Column):
    """
    A column to represent a many-to-many relationship.

    This is different from belongs to/has many because with those, every child has only one parent.  With a many-to-many
    relationship, both models can have multiple relatives from the other model.  In order to support this, it's necessary
    to have a third model (the pivot model) that records the relationships.  In general this table just needs three
    columns: it's own id, and then one column for each other model to store the id of the related records.
    You can specify the names of these columns but it also follows the standard naming convention by default:
    take the class name, convert it to snake case, and append `_id`.

    Note, there is a variation on this (`ManyToManyWithData`) where additional data is stored in the pivot table
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
        thingies = clearskies.columns.ManyToMany(
            related_model_class=ThingyReference,
            pivot_model_class=ThingyToWidgetReference,
        )
        thingy_ids = clearskies.columns.ManyToManyIdReference("thingies")

    class Thingy(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies'columns.String()
        widgets = clearskies.columns.ManyToMany(
            related_model_class=WidgetReference,
            pivot_model_class=ThingyToWidgetReference,
        )
        widget_ids = clearskies.columns.ManyToManyIdReference("widgets")

    def my_application(widgets, thingies):
        thing_1 = thingies.create({"name": "Thing 1"})
        thing_2 = thingies.create({"name": "Thing 2"})
        widget = widgets.create({
            "name": "Widget 1",
            "thingies": [thing_1.id, thing_2.id],
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
        "thingies": [...widget.thingy_ids, some_other_id],
    })

    widget.save({
        "thingies": [id for id in widget.thingy_ids if id != "some_id_to_remove"]
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
    default = configs.StringList(default=None)

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.StringListOrCallable(default=None)

    @parameters_to_properties.parameters_to_properties
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
