from __future__ import annotations
from typing import TYPE_CHECKING, overload, Self, Type

from clearskies.columns import CategoryTreeChildren

if TYPE_CHECKING:
    from clearskies import Model

class CategoryTreeDescendents(CategoryTreeChildren):
    @overload
    def __get__(self, instance: None, parent: Type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, parent: Type[Model]) -> Model:
        pass

    def __get__(self, model, parent):
        if model is None:
            return self # type:  ignore

        return self.relatives(model, include_all=True)
