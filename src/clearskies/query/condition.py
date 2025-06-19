class Condition:
    """
    Parses a condition string, e.g. "column=value" or "table.column<=other_value".

    Allowed operators: ["<=>", "!=", "<=", ">=", ">", "<", "=", "in", "is not null", "is null", "is not", "is", "like"]

    NOTE: Not all backends support all operators, so make sure the condition you are building works for your backend

    This is safe to use with untrusted input because it expects a stringent and easy-to-verify format.  The incoming
    string must be one of these patterns:

     1. [column_name][operator][value]
     2. [table_name].[column_name][operator][value]

    SQL-like syntax is allowed, so:

     1. Spaces are optionally allowed around the operator.
     2. Backticks are optionally allowd around the table/column name.
     3. Single quotes are optionally allowed around the values.
     4. operators are case-insensitive.

    In the case of an IN operator, the parser expects a series of comma separated values enclosed in parenthesis,
    with each value optionally enclosed in single quotes.  This parsing is very simple and there is not currently a way
    to escape commas or single quotes.

    NOTE: operators (when they are english words, of course) are always output in all upper-case.

    Some examples:

    ```python
    condition = Condition("id=asdf-qwerty")  # note: same results for: Condition("id = asdf-qwerty")
    print(condition.table_name)  # prints ''
    print(condition.column_name)  # prints 'id'
    print(condition.operator)  # prints '='
    print(condition.values)  # prints ['asdf-qwerty']
    print(condition.parsed)  # prints 'id=%s'

    condition = Condition("orders.status_id in ('ACTIVE', 'PENDING')")
    print(condition.table_name)  # prints 'orders'
    print(condition.column_name)  # prints 'status_id'
    print(condition.operator)  # prints 'IN'
    print(condition.values)  # prints ['ACTIVE', 'PENDING']
    print(condition.parsed)  # prints 'status_id IN (%s, %s)'
    ```
    """

    """
    The name of the table this condition is searching on (if there is one).
    """
    table_name: str = ""

    """
    The name of the column the condition is searching.
    """
    column_name: str = ""

    """
    The operator we are searching with (e.g. '=', '<=', etc...)
    """
    operator: str = ""

    """
    The values the condition is searching for.

    Note this is always a list, although most of the time there is only one value in the list.  Multiple values
    are only present when searching with the IN operator.
    """
    values: list[str] = []

    """
    An SQL-ready string
    """
    parsed: str = ""

    """
    The original condition string
    """
    _raw_condition: str = ""

    """
    The list of operators we can match

    Note: the order is very important because this list is used to find the operator in the condition string.
    As a result, the order of the operators in this list is important.  The condition matching algorithm used
    below will select whichever operator matches earlier in the string, but there are some operators that
    start with the same characters: '<=>' and '<=', as well as 'is', 'is null', 'is not', etc...  This leaves
    room for ambiguity since all of these operators will match at the same location.  In the event of a "tie" the
    algorithm gives preference to the first matching operator.  Therefore, for ambiguous operators, we put the
    longer one first, which means it matches first, and so a condition with a '<=>' operator won't accidentally
    match to the '<=' operator.
    """
    operators: list[str] = [
        "<=>",
        "!=",
        "<=",
        ">=",
        ">",
        "<",
        "=",
        "in",
        "is not null",
        "is null",
        "is not",
        "is",
        "like",
    ]

    operator_lengths: dict[str, int] = {
        "<=>": 3,
        "<=": 2,
        ">=": 2,
        "!=": 2,
        ">": 1,
        "<": 1,
        "=": 1,
        "in": 4,
        "is not null": 12,
        "is null": 8,
        "is not": 8,
        "is": 4,
        "like": 6,
    }

    # some operators require spaces around them
    operators_for_matching: dict[str, str] = {
        "like": " like ",
        "in": " in ",
        "is not null": " is not null",
        "is null": " is null",
        "is": " is ",
        "is not": " is not ",
    }

    operators_with_simple_placeholders: dict[str, bool] = {
        "<=>": True,
        "<=": True,
        ">=": True,
        "!=": True,
        "=": True,
        "<": True,
        ">": True,
    }

    operators_without_placeholders: dict[str, bool] = {
        "is not null": True,
        "is null": True,
    }

    def __init__(self, condition: str):
        self._raw_condition = condition
        lowercase_condition = condition.lower()
        self.operator = ""
        matching_index = len(condition)
        # figure out which operator comes earliest in the string: make sure and check all so we match the
        # earliest operator so we don't get unpredictable results for things like 'age=name<=5'.  We want
        # our operator to **ALWAYS** match whatever comes first in the condition string.
        for operator in self.operators:
            try:
                operator_for_match = self.operators_for_matching.get(operator, operator)
                index = lowercase_condition.index(operator_for_match)
            except ValueError:
                continue
            if index < matching_index:
                matching_index = index
                self.operator = operator

        if not self.operator:
            raise ValueError(f"No supported operators found in condition {condition}")

        self.column_name = condition[:matching_index].strip().replace("`", "")
        value = condition[matching_index + self.operator_lengths[self.operator] :].strip()
        if value and (value[0] == "'" and value[-1] == "'"):
            value = value.strip("'")
        self.values = self._parse_condition_list(value) if self.operator == "in" else [value]
        self.table_name = ""
        if "." in self.column_name:
            [self.table_name, self.column_name] = self.column_name.split(".")
        column_for_parsed = f"{self.table_name}.{self.column_name}" if self.table_name else self.column_name

        if self.operator in self.operators_without_placeholders:
            self.values = []

        self.operator = self.operator.upper()
        self.parsed = self._with_placeholders(
            column_for_parsed, self.operator, self.values, escape=False if self.table_name else True
        )

    def _parse_condition_list(self, value):
        if value[0] != "(" and value[-1] != ")":
            raise ValueError(f"Invalid search value {value} for condition.  For IN operator use `IN (value1,value2)`")

        # note: this is not very smart and will mess things up if there are single quotes/commas in the data
        return list(map(lambda value: value.strip().strip("'"), value[1:-1].split(",")))

    def _with_placeholders(self, column, operator, values, escape=True, escape_character="`"):
        quote = escape_character if escape else ""
        column = column.replace("`", "")
        upper_case_operator = operator.upper()
        lower_case_operator = operator.lower()
        if lower_case_operator in self.operators_with_simple_placeholders:
            return f"{quote}{column}{quote}{upper_case_operator}%s"
        if lower_case_operator in self.operators_without_placeholders:
            return f"{quote}{column}{quote} {upper_case_operator}"
        if lower_case_operator == "is" or lower_case_operator == "is not" or lower_case_operator == "like":
            return f"{quote}{column}{quote} {upper_case_operator} %s"

        # the only thing left is "in" which has a variable number of placeholders
        return f"{quote}{column}{quote} IN (" + ", ".join(["%s" for i in range(len(values))]) + ")"


class ParsedCondition(Condition):
    def __init__(self, column_name: str, operator: str, values: list[str], table_name: str = ""):
        self.column_name = column_name
        if operator not in self.operators:
            raise ValueError(f"Unknown operator '{operator}'")
        self.operator = operator
        self.values = values
        self.table_name = table_name
        column_for_parsed = f"{self.table_name}.{self.column_name}" if self.table_name else self.column_name
        self.parsed = self._with_placeholders(
            column_for_parsed, self.operator, self.values, escape=False if self.table_name else True
        )
        self._raw_condition = self.parsed
