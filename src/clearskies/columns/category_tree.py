from typing import Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.columns import BelongsTo


class CategoryTree(BelongsTo):
    """
    The category tree helps you do quick lookups on a typical category tree.

    It's a very niche tool.  In general, graph databases solve this problem better, but
    it's not always worth the effort of spinning up a new kind of database.

    This column needs a special tree table where it will pre-compute and store the
    necessary information to perform quick lookups about relationships in a cateogry
    tree.  So, imagine you have a table that represents a standard category heirarchy:

    ```
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

    ```
    CREATE TABLE category_tree (
      id varchar(255),
      parent_id varchar(255),
      child_id varchar(255),
      is_parent tinyint(1),
      level tinyint(1),
    )
    ```

    Then you would attach this column to your category model as a replacement for a typical BelongsTo relationship:

    ```
    import clearskies

    class Tree(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        parent_id = clearskies.columns.String()
        child_id = clearskies.columns.String()
        is_parent = clearskies.columns.Boolean()
        level = clearskies.columns.Integer()

    class Category(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        parent_id = clearskies.columns.CategoryTree(Tree)
        parent = clearskies.columns.BelongsToRef("parent_id")
        children = clearskies.columns.CategoryTreeChildren("category_tree")
        descendants = clearskies.columns.CategoryTreeDescendants("category_tree")
        ancestors = clearskies.columns.CategoryTreeAncestors("category_tree")
    ```
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

    @parameters_to_properties.parameters_to_properties
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
        where: clearskies.typing | list[clearskies.typing] = []
        default: str | None = None,
        setable: str | Callable | None = None,
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

    def finalize_configuration(self, model_class) -> None:
        self.parent_model_class = model_class
        self.finalize_and_validate_configuration()
