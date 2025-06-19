from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import clearskies.configs
from clearskies import parameters_to_properties
from clearskies.validator import Validator

if TYPE_CHECKING:
    import clearskies.model


class Required(Validator):
    is_required = True

    def check(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        # you'd think that "required" is straight forward and we want an input error if it isn't found.
        # this isn't strictly true though.  If the model already exists, the column has a value in the model already,
        # and the column is completely missing from the input data, then it is actually perfectly fine (because
        # there will still be a value in the column after the save).  However, if the model doesn't exist, then
        # we must require the column in the data with an actual value.
        has_value = False
        has_some_value = False
        if column_name in data:
            has_some_value = True
            if type(data[column_name]) == str:
                has_value = bool(data[column_name].strip())
            else:
                has_value = bool(data[column_name])
        if has_value:
            return ""
        if model and getattr(model, column_name) and not has_some_value:
            return ""
        return f"'{column_name}' is required."
