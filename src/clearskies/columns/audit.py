import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.columns.has_many import HasMany


class Audit(HasMany):
    """
    Enables auditing for a model.

    Specify the audit class to use and attach this column to your model. Everytime the model is created/updated/deleted,
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
    readable_child_columns = configs.ReadableModelColumns(
        "audit_model_class", default=["resource_id", "action", "data", "created_at"]
    )

    """
    Since this column is always populated automatically, it is never directly writeable.
    """
    is_writeable = configs.Boolean(default=False)
    is_searchable = configs.Boolean(default=False)
    _descriptor_config_map = None

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        audit_model_class,
        exclude_columns: list[str] = [],
        mask_columns: list[str] = [],
        foreign_column_name: str | None = None,
        readable_child_columns: list[str] = [],
        where: clearskies.typing.condition | list[clearskies.typing.condition] = [],
        default: str | None = None,
        is_readable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
    ):
        self.child_model_class = self.audit_model_class

    def save_finished(self, model):
        super().save_finished(model)
        old_data = model._previous_data
        new_data = model.get_raw_data()
        exclude_columns = self.exclude_columns
        mask_columns = self.mask_columns
        model_columns = self.get_model_columns()

        if not old_data:
            create_data = {}
            for key in new_data.keys():
                if key in exclude_columns:
                    continue
                if key in model_columns:
                    column_data = model_columns[key].to_json(model)
                else:
                    column_data = {key: new_data[key]}

                create_data = {
                    **create_data,
                    **column_data,
                }
                if key in mask_columns and key in create_data:
                    create_data[key] = "****"
            self.record(model, "create", data=create_data)
            return

        # note that this is fairly simple logic to get started.  It's not going to detect changes that happen
        # in other "tables".  For instance, disconnecting a record by deleting an entry in a many-to-many relationship
        # won't be picked up by this.
        old_model = model.empty_model()
        old_model.data = old_data
        from_data = {}
        to_data = {}
        for column, new_value in new_data.items():
            if column in exclude_columns or column not in old_data:
                continue
            if old_data[column] == new_value:
                continue
            from_data = {
                **from_data,
                **(
                    model_columns[column].to_json(old_model)
                    if column in model_columns
                    else {column: old_data.get(column)}
                ),
            }
            to_data = {
                **to_data,
                **(
                    model_columns[column].to_json(model)
                    if column in model_columns
                    else {column: model._data.get(column)}
                ),
            }
            if column in mask_columns and column in to_data:
                to_data[column] = "****"
                from_data[column] = "****"
        if not from_data and not to_data:
            return

        self.record(
            model,
            "update",
            data={
                "from": from_data,
                "to": to_data,
            },
        )

    def post_delete(self, model):
        super().post_delete(model)
        exclude_columns = self.exclude_columns
        model_columns = self.get_model_columns()
        mask_columns = self.mask_columns

        final_data = {}
        for key in model._data.keys():
            if key in exclude_columns:
                continue
            final_data = {
                **final_data,
                **(model_columns[key].to_json(model) if key in model_columns else {key: model.data.get(key)}),
            }

        for key in mask_columns:
            if key not in final_data:
                continue
            final_data[key] = "****"

        self.child_models.create(
            {
                "class": self.model_class.__name__,
                "resource_id": model.get(self.model_class.id_column_name),
                "action": "delete",
                "data": final_data,
            }
        )

    @property
    def parent_columns(self):
        if self._parent_columns == None:
            self._parent_columns = self.di.build(self.model_class, cache=True).columns()
        return self._parent_columns

    def record(self, model, action, data=None, record_data=None):
        audit_data = {
            "class": self.model_class.__name__,
            "resource_id": model.get(self.model_class.id_column_name),
            "action": action,
        }
        if data is not None:
            audit_data["data"] = data
        if record_data is not None:
            audit_data = {
                **audit_data,
                **record_data,
            }

        self.child_models.create(audit_data)
