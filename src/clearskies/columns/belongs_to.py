from typing import Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.column import Column


class BelongsTo(Column):
    """
    Declares that this model belongs to another - that it has a parent.

    The way that a belongs to relationship works is that the child model (e.g. the one with
    the BelongsTo column) needs to have a column that stores the id of the parent it is related
    to.  So if there are two models, `Category` (the parent) and `Product` (the child) then:

    ```
    import clearskies

    class Product(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        category_id = clearskies.columns.BelongsTo(Category)
        category = clearskies.columns.BelongsToRef(id_column_name="category_id")
    ```

    The opposite of a BelongsTo relationship is a HasMany relationship, so the parent gets that:

    ```
    import clearskies

    class Category(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        products = clearskies.columns.HasMany(Product)
    ```

    Your application then can use them together:

    ```
    def my_thing(products, categories):
        category = categories.create({"name": "Awesome"})
        product_1 = products.create({"name": "thing", "category_id": category.id})
        product_2 = products.create({"name": "thing", "category_id": category.id})

        print(product_1.category.name)

        print({product.id: product.name for product in category.products})

    Note that with the above example you will run into issues with circular references.
    To resolve that, we have to use model reference classes.  A model reference class looks like
    this:

    ```
    import category

    class CategoryReference:
        def get_model_class(self):
            return category.Category
    ```

    This class needs to be defined in a different file than the model class it references.  You then
    attach this class instead of your model class to the column configuration:

    ```
    class Product(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        category_id = clearskies.columns.BelongsTo(CategoryReference)
        category = clearskies.columns.BelongsToRef(id_column_name="category_id")
    ```

    """

    """ The model class we belong to. """
    parent_model_class = configs.ModelClass(required=True)

    """
    The name of the property used to fetch the parent model itself.

    Note that this isn't set explicitly, but by adding a parent_reference column to the model.
    """
    model_column_name = configs.String()

    """
    The list of columns from the parent that should be included when converting this column to JSON.
    """
    readable_parent_columns = configs.ReadableModelColumns("parent_model_class")

    """
    The type of join to use when searching on the parent.
    """
    join_type = configs.Select(["LEFT", "INNER", "RIGHT"], default="LEFT")

    """
    Any additional conditions to place on the parent table when finding related records.
    """
    where = configs.Conditions()

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        parent_model_class,
        readable_parent_columns: list[str] = [],
        join_type: str | None = None,
        where: clearskies.typing.condition | list[clearskies.typing.condition] = [],
        default: str | None = None,
        setable: str | Callable | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
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
