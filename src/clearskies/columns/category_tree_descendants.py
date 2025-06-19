from __future__ import annotations

from typing import TYPE_CHECKING, Self, Type, overload

from clearskies.columns import CategoryTreeChildren

if TYPE_CHECKING:
    from clearskies import Model


class CategoryTreeDescendants(CategoryTreeChildren):
    """
    Return all descendants from a category tree column.

    See the CategoryTree column for usage examples.

    The descendants are the recursive children of a given category.  So, given the following tree:

    ```
    Root/
    ├─ Sub/
    │  ├─ Sub Sub/
    │  │  ├─ Sub Sub Sub/
    ├─ Another Child/

    The descendants of `Root` are `["Sub", "Sub Sub", "Sub Sub Sub", "Another Child"]`.
    """

    _descriptor_config_map = None

    @overload
    def __get__(self, instance: None, cls: type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type[Model]) -> Model:
        pass

    def __get__(self, model, cls):
        if model is None:
            self.model_class = cls
            return self  # type:  ignore

        return self.relatives(model, include_all=True)
