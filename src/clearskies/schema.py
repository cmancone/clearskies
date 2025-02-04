from __future__ import annotations
from typing import Self, TYPE_CHECKING

if TYPE_CHECKING:
    from clearskies import Column

class Schema:
    """
    Define a schema by extending and declaring columns.

    ```
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

    _columns: dict[str, Column] = {}

    @classmethod
    def get_columns(cls: type[Self], overrides={}) -> dict[str, Column]:
        """
        Returns an ordered dictionary with the configuration for the columns

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
            if not hasattr(attribute, "setable") and not hasattr(attribute, "default"):
                continue

            if attribute_name in overrides:
                columns[attribute_name] = overrides[attribute_name]
                del overrides[attribute_name]
            attribute.finalize_configuration(cls, attribute_name)
            columns[attribute_name] = attribute

        for (attribute_name, column) in overrides.items():
            columns[attribute_name] = column  # type: ignore

        if not overrides:
            cls._columns = columns
        return columns
