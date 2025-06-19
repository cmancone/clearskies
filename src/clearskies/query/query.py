from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from .condition import Condition
from .join import Join
from .sort import Sort

if TYPE_CHECKING:
    from clearskies import Model


class Query:
    """
    Track the various aspects of a query.

    This is mostly just used by the Model class to keep track of a list request.
    """

    """
    The model class
    """
    model_class: type[Model] = None  # type: ignore

    """
    The list of where conditions for the query.
    """
    conditions: list[Condition] = []

    """
    The conditions, but organized by column.
    """
    conditions_by_column: dict[str, list[Condition]] = {}

    """
    Joins for the query.
    """
    joins: list[Join] = []

    """
    The sort directives for the query
    """
    sorts: list[Sort] = []

    """
    The maximum number of records to return.
    """
    limit: int = 0

    """
    Pagination information (e.g. start/next_token/etc... the details depend on the backend.
    """
    pagination: dict[str, Any] = {}

    """
    A list of select statements.
    """
    selects: list[str] = []

    """
    Whether or not to just select all columns.
    """
    select_all: bool = True

    """
    The name of the column to group by.
    """
    group_by = ""

    def __init__(
        self,
        model_class: type[Model],
        conditions: list[Condition] = [],
        joins: list[Join] = [],
        sorts: list[Sort] = [],
        limit: int = 0,
        group_by: str = "",
        pagination: dict[str, Any] = {},
        selects: list[str] = [],
        select_all: bool = True,
    ):
        self.model_class = model_class
        self.conditions = [*conditions]
        self.joins = [*joins]
        self.sorts = [*sorts]
        self.limit = limit
        self.group_by = group_by
        self.pagination = {**pagination}
        self.selects = [*selects]
        self.select_all = select_all
        self.conditions_by_column = {}
        if conditions:
            for condition in conditions:
                if condition.column_name not in self.conditions_by_column:
                    self.conditions_by_column[condition.column_name] = []
                self.conditions_by_column[condition.column_name].append(condition)

    def as_kwargs(self):
        """Return the properties of this query as a dictionary so it can be used as kwargs when creating another one."""
        return {
            "model_class": self.model_class,
            "conditions": self.conditions,
            "joins": self.joins,
            "sorts": self.sorts,
            "limit": self.limit,
            "group_by": self.group_by,
            "pagination": self.pagination,
            "selects": self.selects,
            "select_all": self.select_all,
        }

    def add_where(self, condition: Condition) -> Self:
        self.validate_column(condition.column_name, "filter", table=condition.table_name)
        new_kwargs = self.as_kwargs()
        new_kwargs["conditions"].append(condition)
        return self.__class__(**new_kwargs)

    def add_join(self, join: Join) -> Self:
        new_kwargs = self.as_kwargs()
        new_kwargs["joins"].append(join)
        return self.__class__(**new_kwargs)

    def set_sort(self, sort: Sort, secondary_sort: Sort | None = None) -> Self:
        self.validate_column(sort.column_name, "sort", table=sort.table_name)
        new_kwargs = self.as_kwargs()
        new_kwargs["sorts"] = [sort]
        if secondary_sort:
            new_kwargs["sorts"].append(secondary_sort)

        return self.__class__(**new_kwargs)

    def set_limit(self, limit: int) -> Self:
        if not isinstance(limit, int):
            raise TypeError(
                f"The limit in a query must be of type int but I received a value of type '{limit.__class__.__name__}'"
            )
        return self.__class__(
            **{
                **self.as_kwargs(),
                "limit": limit,
            }
        )

    def set_group_by(self, column_name) -> Self:
        self.validate_column(column_name, "group")
        return self.__class__(
            **{
                **self.as_kwargs(),
                "group_by": column_name,
            }
        )

    def set_pagination(self, pagination: dict[str, Any]) -> Self:
        return self.__class__(
            **{
                **self.as_kwargs(),
                "pagination": pagination,
            }
        )

    def add_select(self, select: str) -> Self:
        new_kwargs = self.as_kwargs()
        new_kwargs["selects"].append(select)
        return self.__class__(**new_kwargs)

    def set_select_all(self, select_all: bool) -> Self:
        return self.__class__(
            **{
                **self.as_kwargs(),
                "select_all": select_all,
            }
        )

    def validate_column(self: Self, column_name: str, action: str, table: str | None = None) -> None:
        # for now, only validate columns that belong to *our* table.
        # in some cases we are explicitly told the column name
        if table is not None:
            # note that table may be '', in which case it is implicitly "our" table
            if table != "" and table != self.model_class.destination_name():
                return

        # but in some cases we should check and see if it is included with the column name
        column_name = column_name.replace("`", "")
        if "." in column_name:
            parts = column_name.split(".")
            if parts[0] != self.model_class.destination_name():
                return
            column_name = column_name.split(".")[1]

        model_columns = self.model_class.get_columns()
        if column_name not in model_columns:
            raise KeyError(
                f"Cannot {action} by column '{column_name}' for model class {self.model_class.__name__} because this "
                + "column does not exist for the model.  You can suppress this error by adding a matching column "
                + "to your model definition"
            )
