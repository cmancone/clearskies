from .column import Column


class Float(Column):
    def from_database(self, value):
        return float(value)

    def check_search_value(self, value):
        return 'value should be an integer or float' if (type(value) != int and type(value) != float) else ''
