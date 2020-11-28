from .column import Column


class Integer(Column):
    def from_database(self, value):
        return int(value)

