from . import string, has_many
from clearskies.functional.string import title_case_to_snake_case
class Audit(has_many.HasMany):
    """
    Enables auditing for a model.

    Specif the audit class to use and attach this to your model. Everytime the model is created/updated/deleted,
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

    With `exclude_columns` you can specify some names of columns to ignore.  If an update happens and only columns
    in `exclude_columns` are being set, then a history entry will not be created.  Also, these columns will
    not be included in the audit record.
    """
    _parent_columns = None

    required_configs = [
        'audit_models_class',
    ]

    my_configs = [
        'child_models_class',
        'exclude_columns',
        'foreign_column_name',
        'is_readable',
        'readable_child_columns',
        'parent_class_name',
        'parent_id_column_name',
    ]

    def __init__(self, di):
        super().__init__(di)

    def configure(self, name, configuration, model_class):
        if 'audit_models_class' not in configuration:
            raise KeyError(
                "Missing required configuration value 'audit_models_class' for column '{name}' in model class " +
                f"'{model_class.__name__}'"
            )
        self.validate_models_class(configuration['audit_models_class'])
        has_many_configuration = {
            **configuration,
            'child_models_class': configuration.get('audit_models_class'),
            'foreign_column_name': 'resource_id',
            'is_readable': True,
            'readable_child_columns': ['resource_id', 'action', 'data', 'created_at'],
            'parent_class_name': model_class.__name__,
            'exclude_columns': configuration.get('exclude_columns', []),
        }
        super().configure(name, has_many_configuration, model_class)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = f"Configuration error for '{self.name}' in '{self.model_class.__name__}':"
        audit_columns = self.di.build(configuration['audit_models_class'], cache=True).raw_columns_configuration()
        parent_columns = self.di.build(self.model_class, cache=True).raw_columns_configuration()
        required_audit_columns = {
            "class": string.String,
            "resource_id": True,
            "action": string.String,
            "data": True,
            "created_at": True,
        }
        for (column_name, column_type) in required_audit_columns.items():
            if column_name not in audit_columns:
                raise ValueError(f"{error_prefix} audit models class does not have the required column '{column_name}'")
            if column_type == True:
                continue
            if audit_columns[column_name]['class'] != column_type:
                raise ValueError(f"{error_prefix} the '{column_name}' column in the audit models class should have a type of " + column_type.__name__ + " but it has something else")

        if 'exclude_columns' in configuration:
            exclude_columns = configuration['exclude_columns']
            if not hasattr(exclude_columns, '__iter__'):
                raise ValueError(
                    f"{error_prefix} 'exclude_columns' should be an iterable " + \
                    'with the list of columns to exclude.'
                )
            if isinstance(exclude_columns, str):
                raise ValueError(
                    f"{error_prefix} 'exclude_columns' should be an iterable " + \
                    'with the list of child columns to output.'
                )
            for column_name in exclude_columns:
                if column_name not in parent_columns:
                    raise ValueError(
                        f"{error_prefix} 'exclude_columns' references column named '{column_name}' but this" + \
                        ' column does not exist in the original model class.'
                    )

    def provide(self, data, column_name):
        return super().provide(data, column_name).where("class=" + self.config('parent_class_name'))

    def save_finished(self, model):
        super().save_finished(model)
        old_data = model._previous_data
        new_data = model.data
        exclude_columns = self.config('exclude_columns')
        parent_columns = self.parent_columns

        if not old_data:
            self.child_models.create({
                'class': self.config('parent_class_name'),
                'resource_id': model.get(self.config('parent_id_column_name')),
                'action': 'create',
                'data': {key: parent_columns[key].to_json(model) for key in new_data.keys() if key not in exclude_columns},
            })
            return

        # note that this is fairly simple logic to get started.  It's not going to detect changes that happen
        # in other "tables".  For instance, disconnecting a record by deleting an entry in a many-to-many relationship
        # won't be picked up by this.
        old_model = model.empty_model()
        old_model.data = old_data
        changes = {}
        for (column, new_value) in new_data.items():
            if column in exclude_columns or column not in old_data:
                continue
            if old_data[column] == new_value:
                continue
            changes[column] = {
                "from": parent_columns[column].to_json(old_model),
                "to": parent_columns[column].to_json(model)
            }
        if not changes:
            return

        self.child_models.create({
            'class': self.config('parent_class_name'),
            'resource_id': model.get(self.config('parent_id_column_name')),
            'action': 'update',
            'data': changes,
        })

    def post_delete(self, model):
        super().post_delete(model)
        exclude_columns = self.config('exclude_columns')
        self.child_models.create({
            'class': self.config('parent_class_name'),
            'resource_id': model.get(self.config('parent_id_column_name')),
            'action': 'delete',
            'data': {key: value for (key, value) in model.data.items() if key not in exclude_columns},
        })

    @property
    def parent_columns(self):
        if self._parent_columns == None:
            self._parent_columns = self.di.build(self.model_class, cache=True).columns()
        return self._parent_columns

def build_column_config(name, column_class, **kwargs):
    return (name, {**{"class": column_class}, **kwargs})
def audit(name, **kwargs):
    return build_column_config(name, Audit, **kwargs)
