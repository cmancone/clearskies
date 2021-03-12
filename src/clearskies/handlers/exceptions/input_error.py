class InputError(Exception):
    def __init__(self, errors):
        super().__init__(self, 'Input Error')
        self.errors = errors
