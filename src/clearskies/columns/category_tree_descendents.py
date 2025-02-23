from __future__ import annotations
from typing import TYPE_CHECKING, overload, Self, Type

from clearskies.columns import CategoryTreeChildren

if TYPE_CHECKING:
    from clearskies import Model

class CategoryTreeDescendents(CategoryTreeChildren):
    _descriptor_config_map = None

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

        return self.relatives(model, include_all=True)
