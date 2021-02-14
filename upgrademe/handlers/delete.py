from collections import OrderedDict
from .base import Base


class Delete(Base):
    _models = None

    def __init__(self, request, authentication, models):
        super().__init__(request, authentication)
        self._models = models

    def handle(self):
        input_data = self.json_body()
        if 'id' not in input_data:
            return self.error("Missing 'id' in request body", 404)
        model_id = int(input_data['id'])
        model = self._models.find(f'id={model_id}')
        if not model.exists:
            return self.error("Not Found", 404)

        model.delete()
        return self.success({})
