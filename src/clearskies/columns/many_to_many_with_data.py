from typing import Callable


from clearskies import configs, parameters_to_properties
from clearskies.columns import ManyToMany


class ManyToManyWithData(ManyToMany):
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
        thingy_id = clearskies.columns.BelongsTo(ThingyReference)
        widget_id = clearskies.columns.BelongsTo(WidgetReference)
        some_info = clearskies.columns.String()

    class Widget(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies'columns.String()
        thingies = clearskies.columns.ManyToMany(
            related_model_class=ThingyReference,
            pivot_model_class=ThingyToWidgetReference,
        )
        thingy_ids = clearskies.columns.ManyToManyIdReference("thingies")
        thingy_widgets = clearskies.columns.ManyToManyPivotReference("thingies")

    class Thingy(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies'columns.String()
        some_ref = clearskies.columns.String(validators=clearskies.validators.Unique())
        widgets = clearskies.columns.ManyToMany(
            related_model_class=WidgetReference,
            pivot_model_class=ThingyToWidgetReference,
        )
        widget_ids = clearskies.columns.ManyToManyIdReference("widgets")
        thingy_widgets = clearskies.columns.ManyToManyPivotReference("widgets")

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
    setable_columns = configs.ReadableModelColumns("pivot_model_class")

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
    default = configs.ListAnyDict(default=None)

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.ListAnyDictOrCallable(default=None)


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
        validators: clearskies.typing.validators | list[clearskies.typing.validators] = [],
        on_change_pre_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_post_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_save_finished: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
    ):
        pass
