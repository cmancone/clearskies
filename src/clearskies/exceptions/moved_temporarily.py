class MovedTemporarily(Exception):
    def __init__(self, location):
        super().__init__(self, location)
