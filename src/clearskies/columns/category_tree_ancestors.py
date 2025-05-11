from __future__ import annotations
from typing import TYPE_CHECKING, overload, Self

from clearskies.columns.category_tree_children import CategoryTreeChildren

if TYPE_CHECKING:
    from clearskies import Model

class CategoryTreeAncestors(CategoryTreeChildren):
    """
    A column to fetch the ancestors from a category tree column.

    See the CategoryTree column for usage examples.

    The ancestors are all parents of a given category, starting from the root category and working
    down to the direct parent.  So, given the following category tree:

    ```
    Root/
    ├─ Sub/
    │  ├─ Sub Sub/
    │  │  ├─ Sub Sub Sub/
    ├─ Another Child/
    ```

    The ancesotrs of `Sub Sub Sub` are `["Root", "Sub", "Sub Sub"]` while the ancestors of `Another Child`
    are `["Root"]`
    """

    _descriptor_config_map = None

    @overload
    def __get__(self, instance: None, cls: type) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type) -> Model:
        pass

    def __get__(self, model, cls):
        if model is None:
            self.model_class = cls
            return self # type:  ignore

        return self.relatives(model, find_parents=True, include_all=True)
