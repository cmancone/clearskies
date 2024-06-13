from abc import ABC, abstractmethod
from .condition_parser import ConditionParser
from typing import Any, Callable, Dict, List, Tuple, Iterator

try:
    from typing_extensions import Self
except ModuleNotFoundError:
    from typing import Self


class Models(ABC, ConditionParser):
    # The database connection
    _backend = None
    _columns = None
    _model_columns = None
    _next_page_data = None

    query_wheres = None
    query_sorts = None
    query_group_by_column = None
    query_limit = None
    query_pagination = None
    query_selects = None
    query_select_all = None
    must_rexecute = True
    must_recount = True
    count = None
    _table_name = None
    _id_column_name = None
    _query_configuration = None

    def __init__(self, backend, columns):
        self._model_columns = None
        self._backend = backend
        self._columns = columns
        self.must_rexecute = True
        self._next_page_data = None
        self.must_recount = True

        self.query_wheres = []
        self.query_sorts = []
        self.query_group_by_column = None
        self.query_joins = []
        self.query_limit = None
        self.query_pagination = {}
        self.query_selects = []
        self.query_select_all = True

    @abstractmethod
    def model_class(self: Self) -> type[Self]:
        """Return the model class that this models object will find/return instances of"""
        pass

    def clone(self: Self) -> Self:
        clone = self.blank()
        clone.query_configuration = self.query_configuration
        return clone

    def blank(self: Self) -> Self:
        return self._build_model()

    def get_table_name(self: Self) -> str:
        if self._table_name is None:
            self._table_name = self.model_class().table_name()
        return self._table_name

    def get_id_column_name(self: Self) -> str:
        if self._id_column_name is None:
            self._id_column_name = self.empty_model().id_column_name
        return self._id_column_name

    @property
    def query_configuration(self: Self) -> Dict[str, Any]:
        return {
            "wheres": [*self.query_wheres],
            "sorts": [*self.query_sorts],
            "group_by_column": self.query_group_by_column,
            "joins": [*self.query_joins],
            "limit": self.query_limit,
            "pagination": self.query_pagination,
            "selects": self.query_selects,
            "select_all": self.query_select_all,
            "table_name": self.get_table_name(),
            "model_columns": self.model_columns,
        }

    @query_configuration.setter
    def query_configuration(self: Self, configuration: Dict[str, Any]):
        self.query_wheres = configuration["wheres"]
        self.query_sorts = configuration["sorts"]
        self.query_group_by_column = configuration["group_by_column"]
        self.query_joins = configuration["joins"]
        self.query_limit = configuration["limit"]
        self.query_pagination = configuration["pagination"]
        self.query_selects = configuration["selects"]
        self.query_select_all = configuration["select_all"]
        self._model_columns = configuration["model_columns"]

    @property
    def model_columns(self: Self):
        if self._model_columns is None:
            self._model_columns = self.empty_model().columns()
        return self._model_columns

    def select(self: Self, selects) -> Self:
        return self.clone().select_in_place(selects)

    def select_in_place(self: Self, selects) -> Self:
        self.query_selects.append(selects)
        self.must_rexecute = True
        self._next_page_data = None
        return self

    def select_all(self: Self, select_all=True) -> Self:
        return self.clone().select_all_in_place(select_all=select_all)

    def select_all_in_place(self: Self, select_all=True) -> Self:
        self.query_select_all = select_all
        self.must_rexecute = True
        self._next_page_data = None
        return self

    def where(self: Self, where: str) -> Self:
        """Adds the given condition to the query and returns a new Models object"""
        return self.clone().where_in_place(where)

    def where_in_place(self: Self, where: str) -> Self:
        """Adds the given condition to the query for the current Models object"""
        condition = self.parse_condition(where)
        self._validate_column(condition["column"], "filter", table=condition["table"])
        self.query_wheres.append(self.parse_condition(where))
        self.must_rexecute = True
        self._next_page_data = None
        self.must_recount = True
        return self

    def join(self: Self, join: str) -> Self:
        return self.clone().join_in_place(join)

    def join_in_place(self: Self, join: str) -> Self:
        self.query_joins.append(self.parse_join(join))
        self.must_rexecute = True
        self._next_page_data = None
        self.must_recount = True
        return self

    def is_joined(self: Self, table_name, alias=None):
        for join in self.query_joins:
            if join["table"] != table_name:
                continue

            if alias and join["alias"] != alias:
                continue

            return join["alias"] if join["alias"] else join["table"]
        return False

    def group_by(self: Self, group_column: str) -> Self:
        return self.clone().group_by_in_place(group_column)

    def group_by_in_place(self: Self, group_column: str) -> Self:
        self._validate_column(group_column, "group")
        self.query_group_by_column = group_column
        self.must_rexecute = True
        self._next_page_data = None
        self.must_recount = True
        return self

    def sort_by(
        self: Self,
        primary_column,
        primary_direction,
        primary_table=None,
        secondary_column=None,
        secondary_direction=None,
        secondary_table=None,
    ) -> Self:
        return self.clone().sort_by_in_place(
            primary_column,
            primary_direction,
            primary_table=primary_table,
            secondary_column=secondary_column,
            secondary_direction=secondary_direction,
            secondary_table=secondary_table,
        )

    def sort_by_in_place(
        self: Self,
        primary_column,
        primary_direction,
        primary_table=None,
        secondary_column=None,
        secondary_direction=None,
        secondary_table=None,
    ) -> Self:
        sorts = [
            {"table": primary_table, "column": primary_column, "direction": primary_direction},
            {"table": secondary_table, "column": secondary_column, "direction": secondary_direction},
        ]
        sorts = filter(lambda sort: sort["column"] is not None and sort["direction"] is not None, sorts)
        self.query_sorts = list(map(lambda sort: self._normalize_and_validate_sort(sort), sorts))
        if len(self.query_sorts) == 0:
            raise ValueError("Missing primary column or direction in call to sort_by")
        self.must_rexecute = True
        self._next_page_data = None
        return self

    def _normalize_and_validate_sort(self: Self, sort):
        if "column" not in sort or not sort["column"]:
            raise ValueError("Missing 'column' for sort")
        if "direction" not in sort or not sort["direction"]:
            raise ValueError("Missing 'direction' for sort: should be ASC or DESC")
        direction = sort["direction"].upper().strip()
        if direction != "ASC" and direction != "DESC":
            raise ValueError(f"Invalid sort direction: should be ASC or DESC, not '{direction}'")
        self._validate_column(sort["column"], "sort", table=sort.get("table"))

        # down the line we may ask the model class what columns we can sort on, but we're good for now
        return {"column": sort["column"], "direction": sort["direction"], "table": sort.get("table")}

    def _validate_column(self: Self, column_name, action, table=None):
        """
        Down the line we may use the model configuration to check what columns are valid sort/group/search targets
        """
        # for now, only validate columns that belong to *our* table.
        # in some cases we are explicitly told the column name
        if table is not None:
            # note that table may be '', in which case it is implicitly "our" table
            if table != "" and table != self.get_table_name():
                return

        # but in some cases we should check and see if it is included with the column name
        column_name = column_name.replace("`", "")
        if "." in column_name:
            parts = column_name.split(".")
            if parts[0] != self.get_table_name():
                return
            column_name = column_name.split(".")[1]

        model_columns = self.model_columns
        if column_name not in model_columns:
            model_class = self.model_class()
            raise KeyError(
                f"Cannot {action} by column '{column_name}' for model class {model_class.__name__} because this "
                + "column does not exist for the model.  You can suppress this error by adding a matching column "
                + "to your model definition"
            )

    def limit(self: Self, limit) -> Self:
        return self.clone().limit_in_place(limit)

    def limit_in_place(self: Self, limit) -> Self:
        self.query_limit = limit
        self.must_rexecute = True
        self._next_page_data = None
        return self

    def pagination(self: Self, **kwargs) -> Self:
        return self.clone().pagination_in_place(**kwargs)

    def pagination_in_place(self: Self, **kwargs) -> Self:
        error = self._backend.validate_pagination_kwargs(kwargs, str)
        if error:
            raise ValueError(
                f"Invalid pagination data for model {self.__class__.__name__} with backend "
                + f"{self._backend.__class__.__name__}. {error}"
            )
        self.query_pagination = kwargs
        self.must_rexecute = True
        self._next_page_data = None
        return self

    def find(self: Self, where: str) -> Self:
        """Returns the first model where condition"""
        return self.clone().where(where).first()

    def __len__(self: Self):
        if self.must_recount:
            self.count = self._backend.count(self.query_configuration, self.empty_model())
            self.must_recount = False
        return self.count

    def __iter__(self: Self) -> Iterator[Self]:
        self._next_page_data = {}
        raw_rows = self._backend.records(
            self.query_configuration,
            self.empty_model(),
            next_page_data=self._next_page_data,
        )
        models = iter([self.model(row) for row in raw_rows])
        return models

    def paginate_all(self: Self) -> List[Self]:
        next_models = self.clone()
        results = list(next_models.__iter__())
        next_page_data = next_models.next_page_data()
        while next_page_data:
            next_models = next_models.clone().pagination(**next_page_data)
            results.extend(next_models.__iter__())
            next_page_data = next_models.next_page_data()
        return results

    def model(self: Self, data) -> Self:
        model = self._build_model()
        model.data = data
        return model

    def _build_model(self: Self) -> Self:
        model_class = self.model_class()
        return model_class(self._backend, self._columns)

    def empty_model(self: Self) -> Self:
        return self.model({})

    def create(self: Self, data: Dict[str, Any]) -> Self:
        empty = self.empty_model()
        empty.save(data)
        return empty

    def first(self: Self) -> Self:
        iter = self.__iter__()
        try:
            return iter.__next__()
        except StopIteration:
            return self.empty_model()

    def columns(self: Self, overrides=None):
        model = self.model({})
        return model.columns(overrides=None)

    def raw_columns_configuration(self: Self):
        return self.model({}).all_columns()

    def allowed_pagination_keys(self: Self) -> List[str]:
        return self._backend.allowed_pagination_keys()

    def validate_pagination_kwargs(self, kwargs: Dict[str, Any], case_mapping: Callable) -> str:
        return self._backend.validate_pagination_kwargs(kwargs, case_mapping)

    def next_page_data(self: Self):
        return self._next_page_data

    def documentation_pagination_next_page_response(self: Self, case_mapping: Callable) -> List[Any]:
        return self._backend.documentation_pagination_next_page_response(case_mapping)

    def documentation_pagination_next_page_example(self: Self, case_mapping: Callable) -> Dict[str, Any]:
        return self._backend.documentation_pagination_next_page_example(case_mapping)

    def documentation_pagination_parameters(self: Self, case_mapping: Callable) -> List[Tuple[Any]]:
        return self._backend.documentation_pagination_parameters(case_mapping)
