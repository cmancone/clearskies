from __future__ import annotations
from typing import Any, TYPE_CHECKING, Type, overload, Self

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
    is a belongs-to relationship the parent has many children, the child belongs to a parent.

    There's an automatic standard where the name of the column in thie child table that stores the
    parent id is made by converting the parent model class name into snake case and then appending
    `_id`.  For instance, if the parent model is called the `DooHicky` class, the child model is
    expected to have a column named `doo_hicky_id`.  If you use a different column name for the
    id in your child model, then just update the `foreign_column_name` proeprty on the `HasMany`
    column accordingly.

    See the BelongsToId class for additional background and usage examples.
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
    So, if the model class is called `ProductCategory`, this becomes `product_category_id`.

    This MUST correspond to the actual name of a column in the child table.
    """
    foreign_column_name = configs.ModelToIdColumn()

    """ Columns from the child table that should be included when converting this column to JSON. """
    readable_child_columns = configs.ReadableModelColumns("child_model_class")

    """ Additional queries to add to searches on the child table. """
    where = configs.Conditions()

    input_output = InputOutput()

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        child_model_class,
        foreign_column_name: str | None = None,
        readable_child_columns: list[str] = [],
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
    def __get__(self, instance: None, cls: Type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: Type[Model]) -> Model:
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
            json: dict[str, Any] = {
                **json,
                **columns[child_id_column_name].to_json(child),
            }
            for column_name in self.readable_child_columns:
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

        for column_name in self.readable_child_columns:
            child_properties.extend(columns[column_name].documentation()) # type: ignore

        child_object = AutoDocObject(
            string.title_case_to_nice(self.child_model_class.__name__),
            child_properties,
        )
        return [AutoDocArray(name if name is not None else self.name, child_object, value=value)]
