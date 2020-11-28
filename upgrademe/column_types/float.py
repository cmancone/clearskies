from .column import Column


class Float(Column):
    def from_database(self, value):
        return float(value)

