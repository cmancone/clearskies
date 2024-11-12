import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.columns import HasMany


class Audit(HasMany):
    """
    Enables auditing for a model.

    Specify the audit class to use and attach this to your model. Everytime the model is created/updated/deleted,
    the audit class will record the action and the changes.  Your audit model must have the following columns:

    | Name        | type     |
    |-------------|----------|
    | class       | str      |
    | resource_id | str      |
    | action      | str      |
    | data        | json     |
    | created_at  | created  |

    The names are not currently adjustable.

     1. Class is a string that records the name of the class that the action happened for.  This allows you to use
        the same audit class for multiple, different, resources.
     2. resource_id is the id of the record which the audit entry is for.
     3. Action is the actual action taken (create/update/delete)
     4. Data is a serialized record of what columns in the record were changed (both their previous and new values)
     5. The time the audit record was created
    """

    """ The model class for the destination that will store the audit data. """
    audit_model_class = configs.ModelClass(required=True)

    """
    A list of columns that shouldn't be copied into the audit record.

    To be clear, these are columns from the model class that the audit column is attached to.
    If only excluded columns are updated then no audit record will be created.
    """
    exclude_columns = configs.ModelColumns()

    """
    A list of columns that should be masked when copied into the audit record.

    With masked columns a generic value is placed in the audit record (e.g. XXXXX) which denotes that
    the column was changed, but it does not record either old or new values.
    """
    mask_columns = configs.ModelColumns()

    """ Columns from the child table that should be included when converting this column to JSON. """
    readable_child_columns = configs.ReadableModelColumns("audit_model_class", default=["resource_id", "action", "data", "created_at"])

    """
    Since this column is always populated automatically, it is never directly writeable.
    """
    is_writeable = configs.Boolean(default=False)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        audit_model_class,
        exclude_columns: list[str] = [],
        mask_columns: list[str] = [],
        foreign_column_name: str | None = None,
        readable_child_columns: list[str] = [],
        where: clearskies.typing.condition | list[clearskies.typing.condition] = None
        default: str | None = None,
        is_readable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_post_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_save_finished: clearskies.typing.actions | list[clearskies.typing.actions] = [],
    ):
        self.child_model_class = self.audit_model_class
