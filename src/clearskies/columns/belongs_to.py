from __future__ import annotations
from typing import Callable, TYPE_CHECKING
from collections import OrderedDict

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.columns.string import String
from clearskies.functional import validations
from clearskies.di.inject import InputOutput

if TYPE_CHECKING:
    from clearskies import Model

class BelongsTo(String):
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
        category = clearskies.columns.BelongsToModel(belongs_to_column_name="category_id")
    ```

    The opposite of a BelongsTo relationship is a HasMany relationship, so the parent gets:

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
        category = clearskies.columns.BelongsToModel(belongs_to_column_name="category_id")
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

    input_output = InputOutput()
    wants_n_plus_one = True
    _allowed_search_operators = ["="]

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
        for (index, where) in enumerate(self.where):
            if callable(where):
                parents = self.di.call_function(where, model=parents)
                if not validations.is_model(parents):
                    raise ValueError(
                        f"Configuration error for {self.model_class.__name__}.{self.name}: when 'where' is a callable, it must return a model class, but when the callable in where entry #{index+1} was called, it returned something else."
                    )
            else:
                parents = parents.where(where)
        return parents

    @property
    def parent_columns(self):
        return self.parent_model_class.get_columns()

    def input_error_for_value(self, value: str, operator: str | None=None) -> str:
        parent_check = super().input_error_for_value(value)
        if parent_check:
            return parent_check
        parent_model = self.parent_model
        matching_parents = parent_model.where(f"{parent_model.id_column_name}={value}")
        matching_parents = matching_parents.where_for_request(
            matching_parents,
            self.input_output.routing_data(),
            self.input_output.get_authorization_data(),
            self.input_output,
        )
        if not len(matching_parents):
            return f"Invalid selection for {self.name}: record does not exist"
        return ""

    def n_plus_one_add_joins(self, model: Model, column_names: list[str] = []) -> Model:
        """
        Add any additional joins to solve the N+1 problem.
        """
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

    def to_json(self, model: Model) -> dict[str, Any]:
        """
        Converts the column into a json-friendly representation
        """
        if not self.readable_parent_columns:
            return super().to_json(model)

        if not self.model_column_name:
            raise ValueError(f"Configuration error for {model.__class__.__name__}: I can't convert to JSON unless I have a BelongsToModel column attached, and it doesn't appear that one has been attached for me.")

        # otherwise return an object with the readable parent columns
        columns = self.parent_columns
        parent = model.__getattr__(self.model_column_name)
        json = OrderedDict()
        if parent.id_column_name not in self.readable_parent_columns:
            json[parent.id_column_name] = list(columns[parent.id_column_name].to_json(parent).values())[0]
        for column_name in self.readable_parent_columns:
            json = {**json, **columns[column_name].to_json(parent)}
        return {
            **super().to_json(model),
            self.model_column_name: json,
        }

    def is_allowed_operator(self, operator, relationship_reference=None):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
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

    def add_search(
        self,
        model: clearskies.model.Model,
        value: str,
        operator: str="",
        relationship_reference: str=""
    ) -> clearskies.model.Model:
        if not relationship_reference:
            return super().add_search(models, value, operator=operator)

        if relationship_reference not in self.parent_columns:
            raise ValueError(
                "I was asked to search on a related column that doens't exist.  This shouldn't have happened :("
            )

        models = self.add_join(model)
        related_column = self.parent_columns[relationship_reference]
        alias = self.join_table_alias()
        return model.where(related_column.build_condition(value, operator=operator, column_prefix=f"{alias}."))
