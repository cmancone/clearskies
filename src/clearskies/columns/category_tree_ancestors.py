from __future__ import annotations
from typing import TYPE_CHECKING, overload, Self

from clearskies.columns.category_tree_children import CategoryTreeChildren

if TYPE_CHECKING:
    from clearskies import Model

class CategoryTreeAncestors(CategoryTreeChildren):

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
