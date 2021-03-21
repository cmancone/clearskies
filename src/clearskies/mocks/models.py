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
    deleted = None
    create_responses = None
    update_responses = None
    search_responses = None
    iterating = None
    iterator_index = None
    iterated = None
    counted = None

    @classmethod
    def reset(cls):
        cls.updated = None
        cls.created = None
        cls.iterated = None
        cls.counted = None
        cls.deleted = None

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
        blank = self.__class__(self._model_configuration)
        blank.create_responses = self.create_responses
        blank.update_responses = self.update_responses
        blank.search_responses = self.search_responses
        return blank


    def add_update_response(self, data):
        if self.update_responses is None:
            self.update_responses = []
        self.update_responses.append(data)

    def add_create_response(self, data):
        if self.create_responses is None:
            self.create_responses = []
        self.create_responses.append(data)

    def add_search_response(self, data):
        # We're expecting a list because a search implicitly returns multiple records.  Technically, we're also
        # okay with tuples, but this is the most straight-forward way to get what we want and should avoid weird
        # errors without causing serious issues later.
        if type(data) != list:
            raise ValueError("A list should be passed into to 'add_search_response'")
        if self.search_responses is None:
            self.search_responses = []
        self.search_responses.append(data)

    def clear_search_responses(self):
        self.search_responses = None

    # our mock models also acts as the backend for the mock model
    def update(self, id, data, model):
        if self.update_responses is None:
            raise ValueError("Must set update data through 'models.add_update_response' before attempting to update")
        if not len(self.update_responses):
            raise ValueError("Ran out of responses while processing an update!")
        if Models.updated is None:
            Models.updated = []
        Models.updated.append({'id': id, 'data': data, 'model': model})
        return self.update_responses.pop(0)

    def create(self, data, model):
        if self.create_responses is None:
            raise ValueError("Must set create data through 'models.add_create_response' before attempting to create")
        if not len(self.create_responses):
            raise ValueError("Ran out of responses while processing an create!")
        if Models.created is None:
            Models.created = []
        Models.created.append({'data': data, 'model': model})
        return self.create_responses.pop(0)

    def delete(self, id, model):
        if Models.deleted is None:
            Models.deleted = []
        Models.deleted.append({'id': id, 'model': model})
        return True

    def count(self, configuration):
        if self.search_responses is None:
            raise ValueError("Must set search data through 'models.add_search_response' before counting")
        if Models.counted == None:
            Models.counted = []
        Models.counted.append(configuration)
        counted = self.search_responses.pop(0)
        return len(counted)

    def iterator(self, configuration):
        if self.search_responses is None:
            raise ValueError("Must set search data through 'models.add_search_response' before counting")
        if Models.iterated == None:
            Models.iterated = []
        Models.iterated.append(configuration)
        self.iterator_index = -1
        self.iterating = self.search_responses.pop(0)
        return self

    def next(self):
        self.iterator_index += 1
        if self.iterator_index >= len(self.iterating):
            raise StopIteration()
        return self.iterating[self.iterator_index]
