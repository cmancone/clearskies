from .column import Column


class Integer(Column):
    def from_database(self, value):
        return int(value)

    def check_search_value(self, value):
        return 'value should be an integer' if type(value) != int else ''
