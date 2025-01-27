from __future__ import annotations
from typing import TYPE_CHECKING, overload, Self

from clearskies.columns import CategoryTreeChildren

if TYPE_CHECKING:
    from clearskies import Model

class CategoryTreeAncestors(CategoryTreeChildren):
    @overload
    def __get__(self, instance: None, parent: type) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, parent: type) -> Model:
        pass

    def __get__(self, model, parent):
        if not model:
            return self # type:  ignore

        return self.relatives(model, find_parents=True, include_all=True)
