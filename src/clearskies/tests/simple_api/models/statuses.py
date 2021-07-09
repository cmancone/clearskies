from clearskies import Models
from . import status


class Statuses(Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def model_class(self):
        return status.Status
