from .string import String


class Select(String):
    required_configs = [
        'values'
    ]

    def check_input(self, model, data):
        if not self.name in data or not data[self.name]:
            return ''
        if data[self.name] in self.config('values'):
            return ''
        return f'Invalid value for {self.name}'
