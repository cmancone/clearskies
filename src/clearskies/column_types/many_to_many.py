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
        'related_models',
        'foreign_column_name_in_pivot',
        'own_column_name_in_pivot',
        'pivot_table',
    ]

    def __init__(self, di):
        self.di = di

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        if self.name[-3:] == '_id' or self.name[-4:] == '_ids':
            raise ValueError(
                f"Invalid name for column '{self.name}' in '{self.model_class.__name__}' - " + \
                "ManyToMany column should not end in '_id' or '_ids'"
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
                'related_models': related_models,
                'pivot_models': pivot_models,
                'foreign_column_name_in_pivot': foreign_column_name,
                'own_column_name_in_pivot': own_column_name,
                'pivot_table': pivot_models.get_table_name(),
            }
        }

    def input_error_for_value(self, value):
        if type(value) != list:
            return f'{self.name} should be a list of ids'
        for id_to_check in value:
            integer_check = super().input_error_for_value(id_to_check)
            if integer_check:
                return integer_check
            if not len(self.config('related_models').where(f"id={id_to_check}")):
                return f"Invalid selection for {self.name}: record {id_to_check} does not exist"
        return ''

    def can_provide(self, column_name):
        return column_name == self.name or column_name == f"{self.name}_ids"

    def provide(self, data, column_name):
        foreign_column_name_in_pivot = self.config('foreign_column_name_in_pivot')
        own_column_name_in_pivot = self.config('own_column_name_in_pivot')
        pivot_table = self.config('pivot_table')
        models = self.config('related_models')
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
            pivot_models = self.config('pivot_models')
            foreign_column_name = self.config('foreign_column_name_in_pivot')
            own_column_name = self.config('own_column_name_in_pivot')
            for to_insert in new_ids-old_ids:
                pivot_models.empty_model().save({
                    foreign_column_name: to_insert,
                    own_column_name: id,
                })

        return data





