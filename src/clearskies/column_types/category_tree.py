import re
from .belongs_to import BelongsTo
from ..autodoc.schema import Array as AutoDocArray
from ..autodoc.schema import Object as AutoDocObject
from ..autodoc.schema import String as AutoDocString
from collections import OrderedDict
class CategoryTree(BelongsTo):
    """
    Builds a tree table for quick lookups in a category heirarchy.

    Imagine you have a model that represents a category heirarchy:

    ```
    CREATE TABLE categories (
      id varchar(255),
      parent_id varchar(255),
      name varchar(255)
    )
    ```

    Where `parent_id` references a record in the same categories table - a category tree!  This works
    fine but it gets tricky when you want to answer the question "what are all the parent categories
    of X category?" or "what are all the child categories of Y category?".  This column class solves that
    by building a tree table that caches this data as the categories are updated.  That table should look
    like this:

    ```
    CREATE TABLE category_tree (
      id varchar(255),
      parent_id varchar(255),
      child_id varchar(255),
      is_parent tinyint(1),
      level tinyint(1),
    )
    ```

    (add indexes as desired).  You then you have your corresponding models:

    ```
    import clearskies

    class CategoryTree(clearskies.Model):
        def __init__(self, cursor_backend, columns):
            super().__init__(cursor_backend, columns)

        def columns_configuration(self):
            return OrderedDict([
                clearskies.column_types.string('parent_id'),
                clearskies.column_types.string('child_id'),
                clearskies.column_types.integer('is_parent'),
                clearskies.column_types.integer('level'),
            ])

    class Category(clearskies.Model):
        def __init__(self, cursor_backend, columns):
            super().__init__(cursor_backend, columns)

        def columns_configuration(self):
            return OrderedDict([
                clearskies.column_types.string('name'),
                clearskies.column_types.category_tree('parent_id', tree_models_class=CategoryTree),
            ])
    ```

    You would then build your cateogry tree normally:

    ```
    # categories object comes in from dependency injection
    root_category = categories.create({'name': 'my root category'})
    sub_category = categories.create({'name': 'my sub category', parent_id=root_category.id})
    alt_sub_category = categories.create({'name': 'my alternate sub category', parent_id=root_category.id})
    sub_sub_category = categories.create({'name': 'my sub-sub category', parent_id=sub_category.id})
    sub_sub_sub_category = categories.create({'name': 'my sub-sub-sub category', parent_id=sub_sub_category.id})
    ```

    and your database would look like this (using auto-incrementing ids for hopeful clarity)

    ```
    $ SELECT * FROM category_tree

    parent_id | child_id | is_parent | level
    1         | 2        | 1         | 0     # sub category
    1         | 3        | 1         | 0     # alt sub category
    1         | 4        | 0         | 0     # sub sub category referencing the root category
    2         | 4        | 1         | 1     # sub sub category referencing the sub category
    1         | 5        | 0         | 0     # sub sub sub category referencing the root category
    2         | 5        | 0         | 1     # sub sub sub category referencing the sub category
    4         | 5        | 1         | 2     # sub sub sub category referencing the sub sub category
    ```

    You can then use various SQL statements to efficiently fetch various pieces of data.

    ```
    # the category tree for a specific category
    SELECT parent_id FROM category_tree WHERE child_id=5 ORDER BY level DESC;
    # all the children of a parent (excluding sub-children)
    SELECT child_id FROM category_tree WHERE parent_id=1 AND is_parent=1
    # All the children of a parent (including sub-children)
    SELECT child_id FROM category_tree WHERE parent_id=1;
    ```

    Of course other kinds of databases are better at this (such as graph databases), but it isn't
    always worth managing another database unless performance is becoming a problem.
    """
    required_configs = [
        'tree_models_class',
    ]

    my_configs = [
        'model_column_name',
        'readable_parent_columns',
        'join_type',
        'tree_parent_id_column_name',
        'tree_child_id_column_name',
        'tree_is_parent_column_name',
        'tree_level_column_name',
        'max_iterations',
        'parent_models_class',
    ]

    def __init__(self, di):
        super().__init__(di)

    def _check_configuration(self, configuration):
        # our parent class is the BelongsTo which needs to know the parent model class.
        # with a category tree, we _are_ our own parent model class, so no need to ask for it.
        super()._check_configuration({
            **configuration,
            'parent_models_class':
            configuration.get('parent_models_class', self.model_class),
        })
        self.validate_models_class(
            configuration['tree_models_class'],
            config_name='tree_models_class',
        )

    def _finalize_configuration(self, configuration):
        return {
            **super()._finalize_configuration({
                **configuration,
                'parent_models_class':
                configuration.get('parent_models_class', self.model_class),
            }),
            **{
                'tree_parent_id_column_name': configuration.get('tree_parent_id_column_name', 'parent_id'),
                'tree_child_id_column_name': configuration.get('tree_child_id_column_name', 'child_id'),
                'tree_is_parent_column_name': configuration.get('tree_is_parent_column_name', 'is_parent'),
                'tree_level_column_name': configuration.get('tree_level_column_name', 'level'),
                'max_iterations': configuration.get('max_iterations', 100),
            }
        }

    @property
    def tree_models(self):
        return self.di.build(self.config('tree_models_class'), cache=True)

    def post_save(self, data, model, id):
        if not model.is_changing(self.name, data):
            return data

        self.update_tree_table(model, id, model.latest(self.name, data))
        return data

    def force_tree_update(self, model):
        self.update_tree_table(model, model.id, model.__getattr__(self.name))

    def update_tree_table(self, model, child_id, direct_parent_id):
        tree_models = self.tree_models
        parent_models = self.parent_models
        model_column_name = self.config('model_column_name')
        tree_parent_id_column_name = self.config('tree_parent_id_column_name')
        tree_child_id_column_name = self.config('tree_child_id_column_name')
        tree_is_parent_column_name = self.config('tree_is_parent_column_name')
        tree_level_column_name = self.config('tree_level_column_name')
        max_iterations = self.config('max_iterations')

        # we're going to be lazy and just delete the data for the current record in the tree table,
        # and then re-insert everything (but we can skip this if creating a new record)
        if model.exists:
            for tree in tree_models.where(f'{tree_child_id_column_name}={child_id}'):
                tree.delete()

        # if we are a root category then we don't have a tree
        if not direct_parent_id:
            return

        is_root = False
        id_column_name = parent_models.id_column_name
        next_parent = parent_models.find(f'{id_column_name}={direct_parent_id}')
        tree = []
        c = 0
        while not is_root:
            c += 1
            if c > max_iterations:
                self._circular(max_iterations)

            tree.append(next_parent.__getattr__(next_parent.id_column_name))
            if not next_parent.__getattr__(self.name):
                is_root = True
            else:
                next_next_parent_id = next_parent.__getattr__(self.name)
                next_parent = parent_models.find(f'{id_column_name}={next_next_parent_id}')

        tree.reverse()
        for (index, parent_id) in enumerate(tree):
            tree_models.create({
                tree_parent_id_column_name: parent_id,
                tree_child_id_column_name: child_id,
                tree_is_parent_column_name: 1 if parent_id == direct_parent_id else 0,
                tree_level_column_name: index,
            })

    def _circular(self, max_iterations):
        raise ValueError(
            f"Error for column '{self.name}' for model class '{self.model_class.__name__}': " +
            f"I've climbed through {max_iterations} parents and haven't found the root yet." +
            "You may have accidentally created a circular cateogry tree.  If not, and your category tree " +
            "really _is_ that deep, then adjust the 'max_iterations' configuration for this column accordingly. "
        )
