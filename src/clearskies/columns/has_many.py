import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies import column_config


class HasMany(column_config.ColumnConfig):
    """
    A column to manage a "has many" relationship.

    In order to manage a has-many relationship, the child model needs a column that stores the
    id of the parent record it belongs to.  Also remember that the reverse of a has-many relationship
    is a belongs-to relationship the parent has many children, the child belongs to a parent.

    There's an automatic standard where the name of the column in thie child table that stores the
    parent id is made by converting the parent model class name into snake case and then appending
    `_id`.  For instance, if the parent model is called the `DooHicky` class, the child model is
    expected to have a column named `doo_hicky_id`.  If you use a different column name for the
    id in your child model, then just update the `foreign_column_name` proeprty on the `HasMany`
    column accordingly.

    See the BelongsTo class for additional background and usage examples.
    """

    """
    HasMany columns are not currently writeable.
    """
    is_writeable = configs.Boolean(default=False)

    """ The model class for the child table we keep our "many" records in. """
    child_model_class = configs.ModelClass(required=True)

    """
    The name of the column in the child table that connects it back to the parent.

    By default this is populated by converting the model class name from TitleCase to snake_case and appending _id.
    So, if the model class is called `ProductCategory`, this becomes `product_category_id`.

    This MUST correspond to the actual name of a column in the child table.
    """
    foreign_column_name = configs.ModelToIdColumn()

    """ Columns from the child table that should be included when converting this column to JSON. """
    readable_child_columns = configs.ReadableModelColumns("child_model_class")

    """ Additional queries to add to searches on the child table. """
    where = configs.Conditions()

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        child_model_class,
        foreign_column_name: str | None = None,
        readable_child_columns: list[str] = [],
        where: clearskies.typing.condition | list[clearskies.typing.condition] = [],
        is_readable: bool = True,
        on_change_pre_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_post_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_save_finished: clearskies.typing.actions | list[clearskies.typing.actions] = [],
    ):
        pass
