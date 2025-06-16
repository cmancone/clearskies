from __future__ import annotations
from typing import Any, TYPE_CHECKING, overload, Self

import clearskies.typing
import clearskies.parameters_to_properties
from clearskies import configs
from clearskies.functional import string, validations
from clearskies.di.inject import InputOutput
from clearskies.column import Column
from clearskies.autodoc.schema import Array as AutoDocArray
from clearskies.autodoc.schema import Object as AutoDocObject
from clearskies.autodoc.schema import Schema as AutoDocSchema

if TYPE_CHECKING:
    from clearskies import Column
    from clearskies import Model

class HasMany(Column):
    """
    A column to manage a "has many" relationship.

    In order to manage a has-many relationship, the child model needs a column that stores the
    id of the parent record it belongs to.  Also remember that the reverse of a has-many relationship
    is a belongs-to relationship: the parent has many children, the child belongs to a parent.

    There's an automatic standard where the name of the column in thie child table that stores the
    parent id is made by converting the parent model class name into snake case and then appending
    `_id`.  For instance, if the parent model is called the `DooHicky` class, the child model is
    expected to have a column named `doo_hicky_id`.  If you use a different column name for the
    id in your child model, then just update the `foreign_column_name` property on the `HasMany`
    column accordingly.

    See the BelongsToId class for additional background and directions on avoiding circular dependency trees.

    ```
    import clearskies

    class Product(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        category_id = clearskies.columns.String()

    class Category(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        products = clearskies.columns.HasMany(Product)

    def test_has_many(products: Product, categories: Category):
        toys = categories.create({"name": "Toys"})
        auto = categories.create({"name": "Auto"})

        # create some toys
        ball = products.create({"name": "Ball", "category_id": toys.id})
        fidget_spinner = products.create({"name": "Fidget Spinner", "category_id": toys.id})
        crayon = products.create({"name": "Crayon", "category_id": toys.id})

        # the HasMany column is an interable of matching records
        toy_names = [product.name for product in toys.products]

        # it specifically returns a models object so you can do more filtering/transformations
        return toys.products.sort_by("name", "asc")

    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(
            test_has_many,
            model_class=Product,
            readable_column_names=["id", "name"],
        ),
        classes=[Category, Product],
    )

    if __name__ == "__main__":
        cli()
    ```

    And if you execute this it will return:

    ```
    {
        "status": "success",
        "error": "",
        "data": [
            {
            "id": "edc68e8d-7fc8-45ce-98f0-9c6f883e4e7f",
            "name": "Ball"
            },
            {
            "id": "b51a0de5-c784-4e0c-880c-56e5bf731dfd",
            "name": "Crayon"
            },
            {
            "id": "06cec3af-d042-4d6b-a99c-b4a0072f188d",
            "name": "Fidget Spinner"
            }
        ],
        "pagination": {},
        "input_errors": {}
    }
    ```

    """

    """
    HasMany columns are not currently writeable.
    """
    is_writeable = configs.Boolean(default=False)
    is_searchable = configs.Boolean(default=False)
    _descriptor_config_map = None

    """ The model class for the child table we keep our "many" records in. """
    child_model_class = configs.ModelClass(required=True)

    """
    The name of the column in the child table that connects it back to the parent.

    By default this is populated by converting the model class name from TitleCase to snake_case and appending _id.
    So, if the model class is called `ProductCategory`, this becomes `product_category_id`.  This MUST correspond to
    the actual name of a column in the child table.  This is used so that the parent can find its child records.

    Example:

    ```
    import clearskies

    class Product(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        my_parent_category_id = clearskies.columns.String()

    class Category(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        products = clearskies.columns.HasMany(Product, foreign_column_name="my_parent_category_id")

    def test_has_many(products: Product, categories: Category):
        toys = categories.create({"name": "Toys"})

        fidget_spinner = products.create({"name": "Fidget Spinner", "my_parent_category_id": toys.id})
        crayon = products.create({"name": "Crayon", "my_parent_category_id": toys.id})
        ball = products.create({"name": "Ball", "my_parent_category_id": toys.id})

        return toys.products.sort_by("name", "asc")

    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(
            test_has_many,
            model_class=Product,
            readable_column_names=["id", "name"],
        ),
        classes=[Category, Product],
    )

    if __name__ == "__main__":
        cli()
    ```

    Compare to the first example for the HasMany class.  In that case, the column in the product model which
    contained the category id was `category_id`, and the `products` column didn't have to specify the
    `foreign_column_name` (since the column name followed the naming rule).  As a result, `category.products`
    was able to find all children of a given category.  In this example, the name of the column in the product
    model that contains the category id was changed to `my_parent_category_id`.  Since this no longer matches
    the naming convention, we had to specify `foreign_column_name="my_parent_category_id"` in `Category.products`,
    in order for the `HasMany` column to find the children.  Therefore, when invoked it returns the same thing:

    ```
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "3cdd06e0-b226-4a4a-962d-e8c5acc759ac",
                "name": "Ball"
            },
            {
                "id": "debc7968-976a-49cd-902c-d359a8abd032",
                "name": "Crayon"
            },
            {
                "id": "0afcd314-cdfc-4a27-ac6e-061b74ee5bf9",
                "name": "Fidget Spinner"
            }
        ],
        "pagination": {},
        "input_errors": {}
    }
    ```
    """
    foreign_column_name = configs.ModelToIdColumn()

    """
    Columns from the child table that should be included when converting this column to JSON.

    You can tell an endpoint to include a `HasMany` column in the response.  If you do this, the columns
    from the child class that are included in the JSON response are determined by `readable_child_column_names`.
    Example:

    ```
    import clearskies

    class Product(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        category_id = clearskies.columns.String()

    class Category(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        products = clearskies.columns.HasMany(Product, readable_child_column_names=["id", "name"])

    def test_has_many(products: Product, categories: Category):
        toys = categories.create({"name": "Toys"})

        fidget_spinner = products.create({"name": "Fidget Spinner", "category_id": toys.id})
        ball = products.create({"name": "Ball", "category_id": toys.id})
        crayon = products.create({"name": "Crayon", "category_id": toys.id})

        return toys

    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(
            test_has_many,
            model_class=Category,
            readable_column_names=["id", "name", "products"],
        ),
        classes=[Category, Product],
    )

    if __name__ == "__main__":
        cli()
    ```

    In this example we're no longer returning a list of products directly.  Instead, we're returning a query
    on the categories nodel and asking the endpoint to also unpack their products.  We set `readable_child_column_names`
    to `["id", "name"]` for `Category.products`, so when the endpoint unpacks the products, it includes those columns:

    ```
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "c8a71c81-fa0e-427d-a166-159f3c9de72b",
                "name": "Office Supplies",
                "products": [
                    {
                        "id": "6d24ffa2-6e1b-4ce9-87ff-daf2ba237c92",
                        "name": "Stapler"
                    },
                    {
                        "id": "3a42cd7d-6804-465e-9fb1-055fafa7fc62",
                        "name": "Chair"
                    }
                ]
            },
            {
                "id": "5a790950-858b-411a-bf5c-1338a28e73d0",
                "name": "Toys",
                "products": [
                    {
                        "id": "d4022224-cc22-49c2-8da9-7a8f9fa7e976",
                        "name": "Fidget Spinner"
                    },
                    {
                        "id": "415fa48e-984a-4703-b6e6-f88f741403c8",
                        "name": "Ball"
                    },
                    {
                        "id": "58328363-5180-441c-b1a8-1b92e12a8f08",
                        "name": "Crayon"
                    }
                ]
            }
        ],
        "pagination": {},
        "input_errors": {}
    }

    ```

    """
    readable_child_column_names = configs.ReadableModelColumns("child_model_class")

    """
    Additional conditions to add to searches on the child table.

    ```
    import clearskies

    class Order(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        total = clearskies.columns.Float()
        status = clearskies.columns.Select(["Open", "In Progress", "Closed"])
        user_id = clearskies.columns.String()

    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        orders = clearskies.columns.HasMany(Order, readable_child_column_names=["id", "status"])
        large_open_orders = clearskies.columns.HasMany(
            Order,
            readable_child_column_names=["id", "status"],
            where=[Order.status.equals("Open"), "total>100"],
        )

    def test_has_many(users: User, orders: Order):
        user = users.create({"name": "Bob"})

        order_1 = orders.create({"status": "Open", "total": 25.50, "user_id": user.id})
        order_2 = orders.create({"status": "Closed", "total": 35.50, "user_id": user.id})
        order_3 = orders.create({"status": "Open", "total": 125, "user_id": user.id})
        order_4 = orders.create({"status": "In Progress", "total": 25.50, "user_id": user.id})

        return user.large_open_orders

    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(
            test_has_many,
            model_class=Order,
            readable_column_names=["id", "total", "status"],
            return_records=True,
        ),
        classes=[Order, User],
    )

    if __name__ == "__main__":
        cli()
    ```

    The above example shows two different ways of adding conditions.  Note that `where` can be either a list or a single
    condition.  If you invoked this you would get:

    ```
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "6ad99935-ac9a-40ef-a1b2-f34538cc6529",
                "total": 125.0,
                "status": "Open"
            }
        ],
        "pagination": {},
        "input_errors": {}
    }
    ```

    Finally, an individual condition can also be a callable that accepts the child model class, adds any desired conditions,
    and then returns the modified model class.  Like usual, this callable can request any defined depenency.  So, for
    instance, the following column definition is equivalent to the example above:

    ```
    class User(clearskies.Model):
        # removing unchanged part for brevity
        large_open_orders = clearskies.columns.HasMany(
            Order,
            readable_child_column_names=["id", "status"],
            where=lambda model: model.where("status=Open").where("total>100"),
        )
    ```
    """
    where = configs.Conditions()

    input_output = InputOutput()

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        child_model_class,
        foreign_column_name: str | None = None,
        readable_child_column_names: list[str] = [],
        where: clearskies.typing.condition | list[clearskies.typing.condition] = [],
        is_readable: bool = True,
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
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

        # this is where we auto-calculate the expected name of our id column in the child model.
        # we can't do it until now because it comes from the model class we are connected to, and
        # we only just get it.
        foreign_column_name_config = self._get_config_object("foreign_column_name")
        foreign_column_name_config.set_model_class(self.child_model_class)
        has_value = False
        try:
            has_value = bool(self.foreign_column_name)
        except KeyError:
            pass

        if not has_value:
            self.foreign_column_name = string.camel_case_to_snake_case(model_class.__name__) + "_id"

        super().finalize_configuration(model_class, name)

    @property
    def child_columns(self) -> dict[str, Column]:
        return self.child_model_class.get_columns()

    @property
    def child_model(self) -> Model:
        return self.di.build(self.child_model_class, cache=True)

    @overload
    def __get__(self, instance: None, cls: type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type[Model]) -> Model:
        pass

    def __get__(self, model, cls):
        if model is None:
            self.model_class = cls
            return self # type:  ignore

        foreign_column_name = self.foreign_column_name
        model_id = getattr(model, model.id_column_name)
        children = self.child_model.where(f"{foreign_column_name}={model_id}")

        if not self.where:
            return children

        for (index, where) in enumerate(self.where):
            if callable(where):
                children = self.di.call_function(where, model=children, **self.input_output.get_context_for_callables())
                if not validations.is_model(children):
                    raise ValueError(
                        f"Configuration error for column '{self.name}' in model '{self.model_class.__name__}': when 'where' is a callable, it must return a models class, but when the callable in where entry #{index+1} was called, it did not return the models class"
                    )
            else:
                children = children.where(where)
        return children

    def __set__(self, model: Model, value: Model) -> None:
        raise ValueError(f"Attempt to set a value to {model.__class__.__name__}.{self.name}: this is not allowed because it is a HasMany column, which is not writeable.")

    def to_json(self, model: Model) -> dict[str, Any]:
        children = []
        columns = self.child_columns
        child_id_column_name = self.child_model_class.id_column_name
        json: dict[str, Any] = {}
        for child in getattr(model, self.name):
            json = {
                **json,
                **columns[child_id_column_name].to_json(child),
            }
            for column_name in self.readable_child_column_names:
                json = {
                    **json,
                    **columns[column_name].to_json(child),
                }
            children.append(json)
        return {self.name: children}

    def documentation(self, name: str | None=None, example: str | None=None, value: str | None=None) -> list[AutoDocSchema]:
        columns = self.child_columns
        child_id_column_name = self.child_model.id_column_name
        child_properties = [columns[child_id_column_name].documentation()]

        for column_name in self.readable_child_column_names:
            child_properties.extend(columns[column_name].documentation()) # type: ignore

        child_object = AutoDocObject(
            string.title_case_to_nice(self.child_model_class.__name__),
            child_properties,
        )
        return [AutoDocArray(name if name is not None else self.name, child_object, value=value)]
