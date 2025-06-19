import re


class Join:
    """
    Parses a join clause.

    Note that this expects a few very specific pattern:

     1. [TYPE] JOIN [right_table_name] ON [left_table_name].[left_column_name]=[right_table_name].[right_column_name]
     2. [TYPE] JOIN [right_table_name] AS [alias] ON [alias].[left_column_name]=[right_table_name].[right_column_name]
     3. [TYPE] JOIN [right_table_name] [alias] ON [alias].[left_column_name]=[right_table_name].[right_column_name]

    NOTE: The allowed join types are ["INNER", "OUTER", "LEFT", "RIGHT"]

    NOTE: backticks are optionally allowed around column and table names.

    Examples:
    ```python
    join = Join("INNER JOIN orders ON users.id=orders.user_id")
    print(f"{join.left_table_name}.{join.left_column_name}")  # prints 'users.id'
    print(f"{join.right_table_name}.{join.right_column_name}")  # prints 'orders.user_id'
    print(join.type)  # prints 'INNER'
    print(join.alias)  # prints ''
    print(join.unaliased_table_name)  # prints 'orders'

    join = Join("JOIN some_long_table_name AS new_table ON old_table.id=new_table.old_id")
    print(f"{join.left_table_name}.{join.left_column_name}")  # prints 'old_table.id'
    print(f"{join.right_table_name}.{join.right_column_name}")  # prints 'new_table.old_id'
    print(join.type)  # prints 'LEFT'
    print(join.alias)  # prints 'new_table'
    print(join.unaliased_table_name)  # prints 'some_long_table_name'
    ```
    """

    """
    The name of the table on the left side of the join
    """
    left_table_name: str = ""

    """
    The name of the column on the left side of the join
    """
    left_column_name: str = ""

    """
    The name of the table on the right side of the join
    """
    right_table_name: str = ""

    """
    The name of the column on the right side of the join
    """
    right_column_name: str = ""

    """
    The type of join (LEFT, RIGHT, INNER, OUTER)
    """
    join_type: str = ""

    """
    An alias for the joined table, if needed
    """
    alias: str = ""

    """
    The actual name of the right table, regardless of alias
    """
    unaliased_table_name: str = ""

    """
    The original join string
    """
    _raw_join: str = ""

    """
    The allowed join types
    """
    _allowed_types = ["INNER", "OUTER", "LEFT", "RIGHT"]

    def __init__(self, join: str):
        self._raw_join = join
        # doing this the simple and stupid way, until that doesn't work.  Yes, it is ugly.
        # Splitting this into two regexps for simplicity: this one does not check for an alias
        matches = re.match(
            "(\\w+\\s+)?join\\s+`?([^\\s`]+)`?\\s+on\\s+`?([^`]+)`?\\.`?([^`]+)`?\\s*=\\s*`?([^`]+)`?\\.`?([^`]+)`?",
            join,
            re.IGNORECASE,
        )
        if matches:
            groups = matches.groups()
            alias = ""
            join_type = groups[0]
            right_table = groups[1]
            first_table = groups[2]
            first_column = groups[3]
            second_table = groups[4]
            second_column = groups[5]
        else:
            matches = re.match(
                "(\\w+\\s+)?join\\s+`?([^\\s`]+)`?\\s+(as\\s+)?(\\S+)\\s+on\\s+`?([^`]+)`?\\.`?([^`]+)`?\\s*=\\s*`?([^`]+)`?\\.`?([^`]+)`?",
                join,
                re.IGNORECASE,
            )
            if not matches:
                raise ValueError(f"Specified join condition, '{join}' does not appear to be a valid join statement")
            groups = matches.groups()
            join_type = groups[0]
            right_table = groups[1]
            alias = groups[3]
            first_table = groups[4]
            first_column = groups[5]
            second_table = groups[6]
            second_column = groups[7]

        # which is the left table and which is the right table?
        match_by = alias if alias else right_table
        if first_table == match_by:
            self.left_table_name = second_table
            self.left_column_name = second_column
            self.right_table_name = first_table
            self.right_column_name = first_column
        elif second_table == match_by:
            self.left_table_name = first_table
            self.left_column_name = first_column
            self.right_table_name = second_table
            self.right_column_name = second_column
        else:
            raise ValueError(
                f"Specified join condition, '{join}' was not understandable because the joined table "
                + "is not referenced in the 'on' clause"
            )

        self.join_type = groups[0].strip().upper() if groups[0] else "INNER"
        self.alias = alias
        self.unaliased_table_name = right_table
