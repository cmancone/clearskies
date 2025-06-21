from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable

import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.autodoc.schema import Object as AutoDocObject
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.autodoc.schema import String as AutoDocString
from clearskies.columns.string import String
from clearskies.di.inject import InputOutput
from clearskies.functional import validations

if TYPE_CHECKING:
    from clearskies import Column, Model


class BelongsToId(String):
    """
    Declares that this model belongs to another - that it has a parent.

    ## Usage

    The way that a belongs to relationship works is that the child model (e.g. the one with
    the BelongsToId column) needs to have a column that stores the id of the parent it is related
    to.  Then you can attach the BelongsToModel class and point it to the column containing the
    id.  If you allow the end-user to set the parent id in a save action, the belongs to column
    will automatically verify that the given id corresponds to an actual record.  Here's a simple
    usage example:

    ```python
    import clearskies


    class Category(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()


    class Product(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        category_id = clearskies.columns.BelongsToId(Category)
        category = clearskies.columns.BelongsToModel("category_id")


    def test_belongs_to(products: Product, categories: Category):
        toys = categories.create({"name": "Toys"})
        auto = categories.create({"name": "Auto"})

        # Note: we set the cateogry by setting "category_id"
        ball = products.create({"name": "ball", "category_id": toys.id})

        # note: we set the category by saving a category model to "category"
        fidget_spinner = products.create({"name": "Fidget Spinner", "category": toys})

        return {
            "ball_category": ball.category.name,
            "fidget_spinner_category": fidget_spinner.category.name,
            "ball_id_check": ball.category_id == ball.category.id,
            "ball_fidget_id_check": fidget_spinner.category_id == ball.category.id,
        }


    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(test_belongs_to),
        classes=[Category, Product],
    )

    if __name__ == "__main__":
        cli()
    ```

    ## Circular Dependency Trees

    The opposite of a BelongsToId relationship is a HasMany relationship.  It's common
    for the child model to contain a BelonsToId column to point to the parent, and then
    have the parent contain a HasMany column to point to the child.  This creates circular
    depenency errors in python.  To work around this, clearskies requires the addition of
    a "model reference" class that looks like this:

    ```python
    import some_model


    class SomeModelReference:
        def get_model_class(self):
            return some_model.SomeModel
    ```

    These have to live in their own file, should use relative imports to import the file containing
    the model, and should not be imported into the module they live in.  So, sticking with the example
    of categories and products, you would have the following directory structure:

    ```
    ├── models
    │   ├── category.py
    │   ├── category_reference.py
    │   ├── product.py
    │   └── product_reference.py
    │
    └── app.py
    ```

    The files would then contain:

    category.py
    ```python
    import clearskies
    import models.product_reference


    class Category(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        products = clearskies.columns.HasMany(product_reference.ProductReference)
    ```

    category_reference.py
    ```python
    from clearskies.model import ModelClassReference
    from . import cateogry


    class CategoryReference(ModelClassReference):
        def get_model_class(self):
            return category.Category
    ```

    product.py
    ```python
    import clearskies
    import models.category_reference


    class Product(clearskies.model.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        category_id = clearskies.columns.BelongsToId(CategoryReference)
        category = clearskies.columns.BelongsToModel("category_id")
    ```

    product_reference.py
    ```python
    from clearskies.model import ModelClassReference
    from . import product


    class ProductReference(ModelClassReference):
        def get_model_class(self):
            return product.Product
    ```
    """

    """ The model class we belong to. """
    parent_model_class = configs.ModelClass(required=True)

    """
    The name of the property used to fetch the parent model itself.

    Note that this isn't set explicitly, but by adding a BelongsToModel column to the model.
    """
    model_column_name = configs.String()

    """
    The list of columns from the parent that should be included when converting this column to JSON.

    When configuring readable columns for an endpoint, you can specify the BelongsToModel column.
    If you do this, you must set readable_parent_columns on the BelongsToId column to specify which
    columns from the parent model should be returned in the response.  See this example:

    ```python
    import clearskies

    class Owner(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()

    class Pet(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        owner_id = clearskies.columns.BelongsToId(
            Owner,
            readable_parent_columns=["id", "name"],
        )
        owner = clearskies.columns.BelongsToModel("owner_id")

    cli = clearskies.contexts.Cli(
        clearskies.endpoints.List(
            Pet,
            sortable_column_names=["id", "name"],
            readable_column_names=["id", "name", "owner"],
            default_sort_column_name="name",
        ),
        classes=[Owner, Pet],
        bindings={
            "memory_backend_default_data": [
                {
                    "model_class": Owner,
                    "records": [
                        {"id": "1-2-3-4", "name": "John Doe"},
                        {"id": "5-6-7-8", "name": "Jane Doe"},
                    ],
                },
                {
                    "model_class": Pet,
                    "records": [
                        {"id": "a-b-c-d", "name": "Fido", "owner_id": "1-2-3-4"},
                        {"id": "e-f-g-h", "name": "Spot", "owner_id": "1-2-3-4"},
                        {"id": "i-j-k-l", "name": "Puss in Boots", "owner_id": "5-6-7-8"},
                    ],
                },
            ],
        }
    )

    if __name__ == "__main__":
        cli()
    ```

    With readable_parent_columns set in the Pet.owner_id column, and owner set in the list configuration,
    The owner id and name are included in the `owner` key of the returned Pet dictionary:

    ```bash
    $ ./test.py  | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "a-b-c-d",
                "name": "Fido",
                "owner": {
                    "id": "1-2-3-4",
                    "name": "John Doe"
                }
            },
            {
                "id": "i-j-k-l",
                "name": "Puss in Boots",
                "owner": {
                    "id": "5-6-7-8",
                    "name": "Jane Doe"
                }
            },
            {
                "id": "e-f-g-h",
                "name": "Spot",
                "owner": {
                    "id": "1-2-3-4",
                    "name": "John Doe"
                }
            }
        ],
        "pagination": {},
        "input_errors": {}
    }
    ```

    """
    readable_parent_columns = configs.ReadableModelColumns("parent_model_class")

    """
    The type of join to use when searching on the parent.
    """
    join_type = configs.Select(["LEFT", "INNER", "RIGHT"], default="LEFT")

    """
    Any additional conditions to place on the parent table when finding related records.

    where should be a list containing a combination of conditions-as-strings, queries built from the columns
    themselves, or callable functions which accept the model and apply filters.  This is primarily used in
    input validation to exclude values as allowed parents.
    """
    where = configs.Conditions()

    input_output = InputOutput()
    wants_n_plus_one = True
    _allowed_search_operators = ["="]
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
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

    @property
    def parent_model(self) -> Model:
        parents = self.di.build(self.parent_model_class, cache=True)
        if not self.where:
            return parents

        return self.apply_wheres(parents)

    def apply_wheres(self, parents: Model) -> Model:
        if not self.where:
            return parents

        for index, where in enumerate(self.where):
            if callable(where):
                parents = self.di.call_function(where, model=parents, **self.input_output.get_context_for_callables())
                if not validations.is_model(parents):
                    raise ValueError(
                        f"Configuration error for {self.model_class.__name__}.{self.name}: when 'where' is a callable, it must return a model class, but when the callable in where entry #{index + 1} was called, it returned something else."
                    )
            else:
                parents = parents.where(where)
        return parents

    @property
    def parent_columns(self) -> dict[str, Any]:
        return self.parent_model_class.get_columns()

    def input_error_for_value(self, value: str, operator: str | None = None) -> str:
        parent_check = super().input_error_for_value(value)
        if parent_check:
            return parent_check
        parent_model = self.parent_model
        matching_parents = parent_model.where(f"{parent_model.id_column_name}={value}")
        matching_parents = self.apply_wheres(matching_parents)
        matching_parents = matching_parents.where_for_request(
            matching_parents,
            self.input_output.routing_data,
            self.input_output.authorization_data,
            self.input_output,
        )
        if not len(matching_parents):
            return f"Invalid selection for {self.name}: record does not exist"
        return ""

    def n_plus_one_add_joins(self, model: Model, column_names: list[str] = []) -> Model:
        """Add any additional joins to solve the N+1 problem."""
        if not column_names:
            column_names = self.readable_parent_columns
        if not column_names:
            return model

        model = self.add_join(model)
        alias = self.join_table_alias()
        parent_id_column_name = self.parent_model.id_column_name
        select_parts = [f"{alias}.{column_name} AS {alias}_{column_name}" for column_name in column_names]
        if parent_id_column_name not in column_names:
            select_parts.append(f"{alias}.{parent_id_column_name} AS {alias}_{parent_id_column_name}")
        return model.select(", ".join(select_parts))

    def add_join(self, model: Model) -> Model:
        parent_table = self.parent_model.destination_name()
        alias = self.join_table_alias()

        if model.is_joined(parent_table, alias=alias):
            return model

        join_type = "LEFT " if self.join_type == "LEFT" else ""
        own_table_name = model.destination_name()
        parent_id_column_name = self.parent_model.id_column_name
        return model.join(
            f"{join_type}JOIN {parent_table} as {alias} on {alias}.{parent_id_column_name}={own_table_name}.{self.name}"
        )

    def join_table_alias(self) -> str:
        return self.parent_model.destination_name() + "_" + self.name

    def is_allowed_operator(self, operator, relationship_reference=None):
        """Proces user data to decide if the end-user is specifying an allowed operator."""
        if not relationship_reference:
            return "="
        parent_columns = self.parent_columns
        if relationship_reference not in self.parent_columns:
            raise ValueError(
                "I was asked to search on a related column that doens't exist.  This shouldn't have happened :("
            )
        return self.parent_columns[relationship_reference].is_allowed_operator(operator)

    def check_search_value(self, value, operator=None, relationship_reference=None):
        if not relationship_reference:
            return self.input_error_for_value(value, operator=operator)
        parent_columns = self.parent_columns
        if relationship_reference not in self.parent_columns:
            raise ValueError(
                "I was asked to search on a related column that doens't exist.  This shouldn't have happened :("
            )
        return self.parent_columns[relationship_reference].check_search_value(value, operator=operator)

    def is_allowed_search_operator(self, operator: str, relationship_reference: str = "") -> bool:
        if not relationship_reference:
            return operator in self._allowed_search_operators
        parent_columns = self.parent_columns
        if relationship_reference not in self.parent_columns:
            raise ValueError(
                "I was asked to check search operators on a related column that doens't exist.  This shouldn't have happened :("
            )
        return self.parent_columns[relationship_reference].is_allowed_search_operator(
            operator, relationship_reference=relationship_reference
        )

    def allowed_search_operators(self, relationship_reference: str = ""):
        if not relationship_reference:
            return self._allowed_search_operators
        parent_columns = self.parent_columns
        if relationship_reference not in self.parent_columns:
            raise ValueError(
                "I was asked for allowed search operators on a related column that doens't exist.  This shouldn't have happened :("
            )
        return self.parent_columns[relationship_reference].allowed_search_operators()

    def add_search(
        self, model: clearskies.model.Model, value: str, operator: str = "", relationship_reference: str = ""
    ) -> clearskies.model.Model:
        if not relationship_reference:
            return super().add_search(model, value, operator=operator)

        if relationship_reference not in self.parent_columns:
            raise ValueError(
                "I was asked to search on a related column that doens't exist.  This shouldn't have happened :("
            )

        model = self.add_join(model)
        related_column = self.parent_columns[relationship_reference]
        alias = self.join_table_alias()
        return model.where(related_column.build_condition(value, operator=operator, column_prefix=f"{alias}."))

    def documentation(
        self, name: str | None = None, example: str | None = None, value: str | None = None
    ) -> list[AutoDocSchema]:
        columns = self.parent_columns
        parent_id_column_name = self.parent_model.id_column_name
        parent_properties = [columns[parent_id_column_name].documentation()]
        parent_id_doc = AutoDocString(name if name is not None else self.name)

        readable_parent_columns = self.readable_parent_columns
        if not readable_parent_columns:
            return [parent_id_doc]

        for column_name in readable_parent_columns:
            if column_name == parent_id_column_name:
                continue
            parent_properties.append(columns[column_name].documentation())

        return [
            parent_id_doc,
            AutoDocObject(
                self.model_column_name,
                parent_properties,
            ),
        ]
