from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.columns.belongs_to_id import BelongsToId

if TYPE_CHECKING:
    from clearskies import Model


class CategoryTree(BelongsToId):
    """
    The category tree helps you do quick lookups on a typical category tree.

    It's a very niche tool.  In general, graph databases solve this problem better, but
    it's not always worth the effort of spinning up a new kind of database.

    This column needs a special tree table where it will pre-compute and store the
    necessary information to perform quick lookups about relationships in a cateogry
    tree.  So, imagine you have a table that represents a standard category heirarchy:

    ```sql
    CREATE TABLE categories (
      id varchar(255),
      parent_id varchar(255),
      name varchar(255)
    )

    `parent_id`, in this case, would be a reference to the `categories` table itself -
    hence the heirarchy.  This works fine  as a starting point but it gets tricky when you want to answer questions like
    "what are all the parent categories of category X?" or "what are all the child categories of category Y?".
    This column class solves that by building a tree table that caches this data as the categories are updated.
    That table should look like this:

    ```sql
    CREATE TABLE category_tree (
      id varchar(255),
      parent_id varchar(255),
      child_id varchar(255),
      is_parent tinyint(1),
      level tinyint(1),
    )
    ```

    Then you would attach this column to your category model as a replacement for a typical BelongsToId relationship:

    ```python
    import clearskies

    class Tree(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend(silent_on_missing_tables=True)

        id = clearskies.columns.Uuid()
        parent_id = clearskies.columns.String()
        child_id = clearskies.columns.String()
        is_parent = clearskies.columns.Boolean()
        level = clearskies.columns.Integer()

    class Category(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend(silent_on_missing_tables=True)

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        parent_id = clearskies.columns.CategoryTree(Tree)
        parent = clearskies.columns.BelongsToModel("parent_id")
        children = clearskies.columns.CategoryTreeChildren("parent_id")
        descendants = clearskies.columns.CategoryTreeDescendants("parent_id")
        ancestors = clearskies.columns.CategoryTreeAncestors("parent_id")

    def test_category_tree(category: Category):
        root_1 = category.create({"name": "Root 1"})
        root_2 = category.create({"name": "Root 2"})
        sub_1_root_1 = category.create({"name": "Sub 1 of Root 1", "parent_id": root_1.id})
        sub_2_root_1 = category.create({"name": "Sub 2 of Root 1", "parent_id": root_1.id})
        sub_sub = category.create({"name": "Sub Sub", "parent_id": sub_1_root_1.id})
        sub_1_root_2 = category.create({"name": "Sub 1 of Root 2", "parent_id": root_2.id})

        return {
            "descendants_of_root_1": [descendant.name for descendant in root_1.descendants],
            "children_of_root_1": [child.name for child in root_1.children],
            "descendants_of_root_2": [descendant.name for descendant in root_2.descendants],
            "ancestors_of_sub_sub": [ancestor.name for ancestor in sub_sub.ancestors],
        }

    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(test_category_tree),
        classes=[Category, Tree],
    )
    cli()
    ```

    And if you invoke the above you will get:

    ```json
    {
        "status": "success",
        "error": "",
        "data": {
            "descendants_of_root_1": ["Sub 1 of Root 1", "Sub 2 of Root 1", "Sub Sub"],
            "children_of_root_1": ["Sub 1 of Root 1", "Sub 2 of Root 1"],
            "descendants_of_root_2": ["Sub 1 of Root 2"],
            "ancestors_of_sub_sub": ["Root 1", "Sub 1 of Root 1"],
        },
        "pagination": {},
        "input_errors": {},
    }
    ```

    In case it's not clear, the definition of these things are:

     1. Descendants: All children under a given category (recursively).
     2. Children: The direct descendants of a given category.
     3. Ancestors: The parents of a given category, starting from the root category.
     4. Parent: the immediate parent of the category.

    """

    """
    The model class that will persist our tree data
    """
    tree_model_class = configs.ModelClass(required=True)

    """
    The column in the tree model that references the parent in the relationship
    """
    tree_parent_id_column_name = configs.ModelColumn("tree_model_class", default="parent_id")

    """
    The column in the tree model that references the child in the relationship
    """
    tree_child_id_column_name = configs.ModelColumn("tree_model_class", default="child_id")

    """
    The column in the tree model that denotes which node in the relationship represents the tree
    """
    tree_is_parent_column_name = configs.ModelColumn("tree_model_class", default="is_parent")

    """
    The column in the tree model that references the parent in a relationship
    """
    tree_level_column_name = configs.ModelColumn("tree_model_class", default="level")

    """
    The maximum expected depth of the tree
    """
    max_iterations = configs.Integer(default=100)

    """
    The strategy for loading relatives.

    Choose whatever one actually works for your backend

     * JOIN: use an actual `JOIN` (e.g. quick and efficient, but mostly only works for SQL backends).
     * WHERE IN: Use a `WHERE IN` condition.
     * INDIVIDUAL: Load each record separately.  Works for any backend but is also the slowest.
    """
    load_relatives_strategy = configs.Select(["join", "where_in", "individual"], default="join")

    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        tree_model_class,
        tree_parent_id_column_name: str = "parent_id",
        tree_child_id_column_name: str = "child_id",
        tree_is_parent_column_name: str = "is_parent",
        tree_level_column_name: str = "level",
        max_iterations: int = 100,
        load_relatives_strategy: str = "join",
        readable_parent_columns: list[str] = [],
        join_type: str | None = None,
        where: clearskies.typing.condition | list[clearskies.typing.condition] = [],
        default: str | None = None,
        setable: str | Callable | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_searchable: bool = True,
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

    def finalize_configuration(self, model_class, name) -> None:
        """
        Finalize and check the configuration.

        This is an external trigger called by the model class when the model class is ready.
        The reason it exists here instead of in the constructor is because some columns are tightly
        connected to the model class, and can't validate configuration until they know what the model is.
        Therefore, we need the model involved, and the only way for a property to know what class it is
        in is if the parent class checks in (which is what happens here).
        """
        self.parent_model_class = model_class
        super().finalize_configuration(model_class, name)

    @property
    def tree_model(self):
        return self.di.build(self.tree_model_class, cache=True)

    def post_save(self, data: dict[str, Any], model: Model, id: int | str) -> None:
        if not model.is_changing(self.name, data):
            return

        self.update_tree_table(model, id, model.latest(self.name, data))
        return

    def force_tree_update(self, model: Model):
        self.update_tree_table(model, getattr(model, model.id_column_name), getattr(model, self.name))

    def update_tree_table(self, model: Model, child_id: int | str, direct_parent_id: int | str) -> None:
        tree_model = self.tree_model
        parent_model = self.parent_model
        tree_parent_id_column_name = self.tree_parent_id_column_name
        tree_child_id_column_name = self.tree_child_id_column_name
        tree_is_parent_column_name = self.tree_is_parent_column_name
        tree_level_column_name = self.tree_level_column_name
        max_iterations = self.max_iterations

        # we're going to be lazy and just delete the data for the current record in the tree table,
        # and then re-insert everything (but we can skip this if creating a new record)
        if model:
            for tree in tree_model.where(f"{tree_child_id_column_name}={child_id}"):
                tree.delete()

        # if we are a root category then we don't have a tree
        if not direct_parent_id:
            return

        is_root = False
        id_column_name = parent_model.id_column_name
        next_parent = parent_model.find(f"{id_column_name}={direct_parent_id}")
        tree = []
        c = 0
        while not is_root:
            c += 1
            if c > max_iterations:
                self._circular(max_iterations)

            tree.append(getattr(next_parent, next_parent.id_column_name))
            if not getattr(next_parent, self.name):
                is_root = True
            else:
                next_next_parent_id = getattr(next_parent, self.name)
                next_parent = model.find(f"{id_column_name}={next_next_parent_id}")

        tree.reverse()
        for index, parent_id in enumerate(tree):
            tree_model.create(
                {
                    tree_parent_id_column_name: parent_id,
                    tree_child_id_column_name: child_id,
                    tree_is_parent_column_name: 1 if parent_id == direct_parent_id else 0,
                    tree_level_column_name: index,
                }
            )

    def _circular(self, max_iterations):
        raise ValueError(
            f"Error for column {self.model_class.__name__}.{self.name}: "
            + f"I've climbed through {max_iterations} parents and haven't found the root yet."
            + "You may have accidentally created a circular cateogry tree.  If not, and your category tree "
            + "really _is_ that deep, then adjust the 'max_iterations' configuration for this column accordingly. "
        )
