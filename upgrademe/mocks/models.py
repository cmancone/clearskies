from ..models import Models as ModelsBase
from ..model import Model as ModelBase
from ..columns import Columns
import pinject


class Model(ModelBase):
    _columns_configuration = None

    def set_columns_configuration(self, columns_configuration):
        self._columns_configuration = columns_configuration

    def columns_configuration(self):
        return self._columns_configuration

class Models(ModelsBase):
    _model_configuration = None
    updated = None
    created = None
    create_responses = None
    update_responses = None
    search_responses = None
    iterating = None
    iterator_index = None

    def __init__(self, model_configuration):
        self._model_configuration = model_configuration
        super().__init__(
            self,
            Columns(pinject.new_object_graph())
        )

    def model(self, data):
        model_class = self.model_class()
        model = model_class(self._backend, self._columns)
        model.set_columns_configuration(self._model_configuration)
        model.data = data
        return model

    def model_class(self):
        return Model

    def blank(self):
        return self.__class__(self._model_configuration)

    def add_update_response(self, data):
        if self.update_responses is None:
            self.update_responses = []
        self.update_responses.append(data)

    def add_create_response(self, data):
        if self.create_responses is None:
            self.create_responses = []
        self.create_responses.append(data)

    def add_search_response(self, data):
        if self.search_responses is None:
            self.search_responses = []
        self.search_responses.append(data)

    # our mock models also acts as the backend for the mock model
    def update(self, id, data, model):
        if self.update_responses is None:
            raise ValueError("Must set update data through 'models.add_update_response' before attempting to update")
        if not len(self.update_responses):
            raise ValueError("Ran out of responses while processing an update!")
        if self.updated is None:
            self.updated = []
        self.updated.append({'id': id, 'data': data, 'model': model})
        return self.update_responses.pop(0)

    def create(self, data, model):
        if self.create_responses is None:
            raise ValueError("Must set create data through 'models.add_create_response' before attempting to create")
        if not len(self.create_responses):
            raise ValueError("Ran out of responses while processing an create!")
        if self.created is None:
            self.created = []
        self.created.append({'data': data, 'model': model})
        return self.create_responses.pop(0)

    def count(self, configuration):
        if self.search_responses is None:
            raise ValueError("Must set search data through 'models.add_search_response' before counting")
        return len(self.search_responses[0])

    def iterator(self, configuration):
        if self.search_responses is None:
            raise ValueError("Must set search data through 'models.add_search_response' before counting")
        self.iterator_index = -1
        self.iterating = self.search_responses.pop(0)

    def next(self, configuration):
        self.iterator_index += 1
        if self.iterator_index >= len(self.iterating):
            raise StopIteration()
        return self.iterating[self.iterator_index]
