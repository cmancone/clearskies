from .integer import Integer
import re


class ManyToMany(Integer):
    """
    Controls a many-to-many relationship.

    This column connects to models via a many-to-many relationship, meaning that a record in either table can
    be associated with multiple records in the other table.  Image you had two models: users and teams, where
    a user can be on more than one team.  To keep track of the mapping, a "pivot" table is required which tracks
    relationships.  In the case of users/teams, you might imagine a table called "users_teams" which has 3 columns:

     - id
     - user_id
     - team_id

    You would then create a many-to-many relationship in both your users model and your teams model that would
    look something like:

    ```
    class User:
      def columns_configuration(self):
        return OrderedDict([
          clearskies.column_types.has_many('teams', related_models_class=Teams, pivot_models_class=UsersTeams),
        ')

    class Team:
      def columns_configuration(self):
        return OrderedDict([
          clearskies.column_types.has_many('users', related_models_class=Users, pivot_models_class=UsersTeams),
        ')
    ```

    Note that `related_models_class` and pivot_models_class receive the model*s* class, not the _model_ class.

    You can attach records to eachother by saving a list of ids via the column name, i.e.:

    ```
    user.save({'teams': [1, 2, 3]})
    team.save({'users': [4, 5, 6]})
    ```

    The many_to_many column will let you easily pull out the related models:

    ```
    print(user.teams)
    # prints [<__main__.Team object>, <__main__.Team object>, <__main__.Team object>]
    ```

    as well as their ids:

    ```
    print(user.teams_ids)
    # prints [1, 2, 3]
    ```
    """
    required_configs = [
        'pivot_models_class',
        'related_models_class',
    ]

    my_configs = [
        'foreign_column_name_in_pivot',
        'own_column_name_in_pivot',
        'pivot_table',
        'readable_related_columns',
        'is_readable',
    ]

    def __init__(self, di):
        self.di = di

    @property
    def is_readable(self):
        is_readable = self.config('is_readable', True)
        # default is_readable to False
        return True if (is_readable and is_readable is not None) else False

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        self.validate_models_class(configuration['pivot_models_class'])
        self.validate_models_class(configuration['related_models_class'])
        if self.name[-3:] == '_id' or self.name[-4:] == '_ids':
            raise ValueError(
                f"Invalid name for column '{self.name}' in '{self.model_class.__name__}' - " + \
                "ManyToMany column should not end in '_id' or '_ids'"
            )

        if configuration.get('is_readable'):
            related_columns = self.di.build(configuration['related_models_class'], cache=False).columns()
            error_prefix = f"Configuration error for '{self.name}' in '{self.model_class.__name__}':"
            if not 'readable_related_columns' in configuration:
                raise ValueError(f"{error_prefix} must provide 'readable_related_columns' if is_readable is set")
            readable_related_columns = configuration['readable_related_columns']
            if not hasattr(readable_related_columns, '__iter__'):
                raise ValueError(
                    f"{error_prefix} 'readable_related_columns' should be an iterable " + \
                    'with the list of child columns to output.'
                )
            if isinstance(readable_related_columns, str):
                raise ValueError(
                    f"{error_prefix} 'readable_related_columns' should be an iterable " + \
                    'with the list of child columns to output.'
                )
            for column_name in readable_related_columns:
                if column_name not in related_columns:
                    raise ValueError(
                        f"{error_prefix} 'readable_related_columns' references column named '{column_name}' but this" + \
                        'column does not exist in the model class.'
                    )
                if not related_columns[column_name].is_readable:
                    raise ValueError(
                        f"{error_prefix} 'readable_related_columns' references column named '{column_name}' but this" + \
                        'column is not readable.'
                    )

    def _finalize_configuration(self, configuration):
        pivot_models = self.di.build(configuration['pivot_models_class'], cache=False)
        related_models = self.di.build(configuration['related_models_class'], cache=False)

        if not configuration.get('foreign_column_name_in_pivot'):
            model_class = related_models.model_class()
            foreign_column_name = re.sub(r'(?<!^)(?=[A-Z])', '_', model_class.__name__.replace('_', '')).lower() + '_id'
        else:
            foreign_column_name = configuration['foreign_column_name_in_pivot']

        if not configuration.get('own_column_name_in_pivot'):
            own_column_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model_class.__name__.replace('_', '')).lower() + '_id'
        else:
            own_column_name = configuration['own_column_name_in_pivot']

        return {
            **super()._finalize_configuration(configuration),
            **{
                'foreign_column_name_in_pivot': foreign_column_name,
                'own_column_name_in_pivot': own_column_name,
                'pivot_table': pivot_models.get_table_name(),
            }
        }

    def input_error_for_value(self, value):
        if type(value) != list:
            return f'{self.name} should be a list of ids'
        related_models = self.related_models
        for id_to_check in value:
            integer_check = super().input_error_for_value(id_to_check)
            if integer_check:
                return integer_check
            if not len(related_models.where(f"id={id_to_check}")):
                return f"Invalid selection for {self.name}: record {id_to_check} does not exist"
        return ''

    def can_provide(self, column_name):
        return column_name == self.name or column_name == f"{self.name}_ids"

    def provide(self, data, column_name):
        foreign_column_name_in_pivot = self.config('foreign_column_name_in_pivot')
        own_column_name_in_pivot = self.config('own_column_name_in_pivot')
        pivot_table = self.config('pivot_table')
        models = self.related_models
        join = f"JOIN {pivot_table} ON {pivot_table}.{foreign_column_name_in_pivot}={models.get_table_name()}.id"
        related_models = models.join(join).where(f"{pivot_table}.{own_column_name_in_pivot}={data['id']}")
        if column_name == self.name:
            return [model for model in related_models]
        return [model.id for model in related_models]

    def to_database(self, data):
        # we can't persist our mapping data to the database directly, so remove anything here
        # and take care of things in post_save
        if self.name in data:
            del data[self.name]
        return data

    def post_save(self, data, model, id):
        # if our incoming data is not in the data array or is None, then nothing has been set and we do not want
        # to make any changes
        if self.name not in data or data[self.name] is None:
            return data

        # figure out what ids need to be created or deleted from the pivot table.
        if not model.exists:
            old_ids = set()
        else:
            old_ids = set(getattr(model, f"{self.name}_ids"))

        new_ids = set(data[self.name])
        to_delete = old_ids-new_ids
        to_create = new_ids-old_ids
        if to_delete:
            related_models = self.config('related_models')
            for model_to_delete in related_models.where("id IN (" + join(',', map(str, to_delete)) + ")"):
                model_to_delete.delete()
        if to_create:
            pivot_models = self.pivot_models
            foreign_column_name = self.config('foreign_column_name_in_pivot')
            own_column_name = self.config('own_column_name_in_pivot')
            for to_insert in new_ids-old_ids:
                pivot_models.empty_model().save({
                    foreign_column_name: to_insert,
                    own_column_name: id,
                })

        return data

    @property
    def pivot_models(self):
        return self.di.build(self.config('pivot_models_class'), cache=False)

    @property
    def related_models(self):
        return self.di.build(self.config('related_models_class'), cache=False)

    @property
    def related_columns(self):
        self.related_models.model_columns

    def input_error_for_value(self, value):
        return f'{self.name} must be an integer' if type(value) != int else ''

    def add_search(self, models, value, operator=None):
        foreign_column_name_in_pivot = self.config('foreign_column_name_in_pivot')
        own_column_name_in_pivot = self.config('own_column_name_in_pivot')
        pivot_table = self.config('pivot_table')
        my_table_name = self.di.build(self.model_class).table_name
        related_table_name = self.related_models.get_table_name()
        join_pivot = f"JOIN {pivot_table} ON {pivot_table}.{own_column_name_in_pivot}={my_table_name}.id"
        # no reason we can't support searching by both an id or a list of ids
        values = value if type(value) == list else [value]
        search = ' IN (' + ', '.join([str(int(val)) for val in value]) + ')'
        return models.join(join_pivot).where(f"{pivot_table}.{foreign_column_name_in_pivot}{search}")

    def to_json(self, model):
        records = []
        columns = self.related_columns
        for related in model.__getattr__(self.name):
            json = OrderedDict()
            json['id'] = int(related.id)
            for column_name in self.config('readable_related_columns'):
                json[column_name] = columns[column_name].to_json(related)
            records.append(json)
        return records

    def response_schema(self, name=None):
        columns = self.related_columns
        schema = []
        if 'id' in columns:
            schema.append(columns['id'].response_schema())
        else:
            schema.append({'name': 'id', 'type': 'integer', 'example': 1})

        for column_name in self.config('readable_related_columns'):
            schema.append(columns[column_name].response_schema())

        return {
            'name': name if name is not None else self.name,
            'type': 'array',
            'schema': {
                'type': 'object',
                'schema': schema,
            }
        }
