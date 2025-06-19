class Sort:
    """Stores a sort directive."""

    """
    The name of the table to sort on.
    """
    table_name: str = ""

    """
    The name of the column to sort on.
    """
    column_name: str = ""

    """
    The direction to sort.
    """
    direction: str = ""

    def __init__(self, table_name: str, column_name: str, direction: str):
        if not column_name:
            raise ValueError("Missing 'column_name' for sort")
        direction = direction.upper().strip()
        if direction != "ASC" and direction != "DESC":
            raise ValueError(f"Invalid sort direction: should be ASC or DESC, not '{direction}'")
        self.table_name = table_name
        self.column_name = column_name
        self.direction = direction
