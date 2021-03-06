from .column import Column


class Integer(Column):
    def from_database(self, value):
        return int(value)

    def check_search_value(self, value):
        return 'value should be an integer' if type(value) != int else ''

    def check_input(self, model, data):
        if not self.name in data or isinstance(data[self.name], int) or data[self.name] == None:
            return ''
        return f'Invalid input: {self.name} must be an integer'
