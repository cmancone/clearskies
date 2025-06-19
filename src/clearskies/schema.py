from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from clearskies import Column


class Schema:
    """
    Define a schema by extending and declaring columns.

    ```python
    from clearskies.schema import Schema
    from clearskies.validators import Required, Unique

    import clearskies.columns


    class Person(Schema):
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String(validators=[Required()])
        date_of_birth = clearskies.columns.Datetime(validators=[Required(), InThePast()])
        email = clearskies.columns.Email()
    ```
    """

    id_column_name: str = ""
    _columns: dict[str, Column] = {}

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        raise NotImplementedError()

    def __init__(self):
        self._data = {}

    @classmethod
    def get_columns(cls: type[Self], overrides={}) -> dict[str, Column]:
        """
        Return an ordered dictionary with the configuration for the columns.

        Generally, this method is meant for internal use.  It just pulls the column configuration
        information out of class attributes.  It doesn't return the fully prepared columns,
        so you probably can't use the return value of this function.  For that, see
        `model.columns()`.
        """
        # no caching if we have overrides
        if cls._columns and not overrides:
            return cls._columns

        overrides = {**overrides}
        columns: dict[str, Column] = OrderedDict()
        for attribute_name in dir(cls):
            attribute = getattr(cls, attribute_name)
            # use duck typing instead of isinstance to decide which attribute is a column.
            # We have to do this to avoid circular imports.
            if not hasattr(attribute, "from_backend") and not hasattr(attribute, "to_backend"):
                continue

            if attribute_name in overrides:
                columns[attribute_name] = overrides[attribute_name]
                del overrides[attribute_name]
            columns[attribute_name] = attribute

        for attribute_name, column in overrides.items():
            columns[attribute_name] = column  # type: ignore

        if not overrides:
            cls._columns = columns

        # now go through and finalize everything.  We have to do this after setting cls._columns, because finalization
        # sometimes depends on fetching the list of columns, so if we do it before caching the answer, we may end up
        # creating circular loops.  I don't *think* this will cause painful side-effects, but we'll find out!
        for column_name, column in cls._columns.items():
            column.finalize_configuration(cls, column_name)

        return columns

    def __bool__(self):
        return False
