from abc import ABC, abstractmethod
import inspect
from .. import model
from typing import Any, Callable, Dict, List, Tuple, Type, Union


class Backend(ABC):
    supports_n_plus_one = False

    @abstractmethod
    def update(self, id: str, data: Dict[str, Any], model: model.Model) -> Dict[str, Any]:
        """
        Updates the record with the given id with the information from the data dictionary
        """
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any], model: model.Model) -> Dict[str, Any]:
        """
        Creates a record with the information from the data dictionary
        """
        pass

    @abstractmethod
    def delete(self, id: str, model: model.Model) -> bool:
        """
        Deletes the record with the given id
        """
        pass

    @abstractmethod
    def count(self, configuration: Dict[str, Any], model: model.Model) -> int:
        """
        Returns the number of records which match the given query configuration
        """
        pass

    @abstractmethod
    def records(
        self, configuration: Dict[str, Any], model: model.Model, next_page_data: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns a list of records that match the given query configuration

        next_page_data is used to return data to the caller.  Pass in an empty dictionary, and it will be populated
        with the data needed to return the next page of results.  If it is still an empty dictionary when returned,
        then there is no additional data.
        """
        pass

    @abstractmethod
    def validate_pagination_kwargs(self, kwargs: Dict[str, Any]) -> str:
        """
        Checks if the given dictionary is valid pagination data for the background.

        Returns a string with an error message, or an empty string if the data is valid
        """
        pass

    @abstractmethod
    def allowed_pagination_keys(self) -> List[str]:
        """
        Returns the list of allowed keys in the pagination kwargs for the backend

        It must always return keys in snake_case so that the auto casing system can
        adjust on the front-end for consistency.
        """
        pass

    @abstractmethod
    def documentation_pagination_next_page_response(self, case_mapping: Callable) -> List[Any]:
        """
        Returns a list of autodoc schema objects describing the contents of the `next_page` dictionary
        in the pagination section of the response
        """
        pass

    @abstractmethod
    def documentation_pagination_parameters(self, case_mapping: Callable) -> List[Tuple[Any]]:
        """
        Returns a list of autodoc schema objects describing the allowed input keys to set pagination.  It should
        return a list of tuples, with each tuple corresponding to an input key.  The first element in the
        tuple should be the schema, and the second should be the description.
        """
        pass

    @abstractmethod
    def documentation_pagination_next_page_example(self, case_mapping: Callable) -> Dict[str, Any]:
        """
        Returns an example (as a simple dictionary) of what the next_page data in the pagination response
        should look like
        """
        pass

    def create_record_with_class(
        self, model_or_class: Union[model.Model, Type[model.Model]], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        This creates a record but, unlike with self.create, does not require a model - just the model class

        Mainly meant for testing because this cheats badly.
        """
        model = self.cheez_model(model_or_class)
        return self.create(data, model)

    def cheez_model(self, model_or_class: Union[model.Model, Type[model.Model]]) -> model.Model:
        """
        Pass in a model or model class, and it returns a (possibly poorly constructed) model

        The backends have some methods mainly meant for testing which accept either a model
        or model class.  We accept the model class because, especially when testing, this is often much easier
        to provide (since you need a columns object to build the model).  In all current cases, these backend
        methods don't actually need a full model - just the table name.  This is quite simple when we have a model,
        because the model can tell you what the table name is.

        It's tricky when we get a model class because that means we need to build the model, but we don't
        have access to a generic model builder.  We could ask the dev to provide a model, but being able to provide just
        a model class will save devs a lot trouble in many cases (especially testing).

        Fortunately, pulling out a table name for the model basically never involves dependencies.  Therefore,
        we will cheat!  We'll just inject gibberish for the arguments of the constructor and hope nothing
        breaks.

        NOTE: If you're here because something broke, and your dependencies actually do matter for determining
        the table name, then you need to do two things:

         1. Consider if you're doing something the wrong way, because that is weird
         2. Just provide the model instead of the model class.
        """
        if inspect.isclass(model_or_class):
            try:
                # the list of args will include 'self' which we don't have to provide, so subtract 1
                nargs = len(inspect.getfullargspec(model_or_class.__init__).args) - 1
                # generate a list of empty strings with a size of nargs and pass that into the constructor
                return model_or_class(*([""] * nargs))
            except AttributeError:
                # if we get here there is no __init__ defined so we don't need to pass arguments
                return model_or_class()
        return model_or_class

    def column_from_backend(self, column, value):
        """
        Manages transformations from the backend

        The idea with this (and `column_to_backend`) is that the transformations to
        and from the backend are mostly determined by the column type - integer, string,
        date, etc...  However, there are cases where these are also backend specific: a datetime
        column may be serialized different ways for different databases, a JSON column must be
        serialized for a database but won't be serialized for an API call, etc...  Therefore
        we mostly just let the column handle this, but we want the backend to be in charge
        in case it needs to make changes.
        """
        return column.from_backend(value)

    def column_to_backend(self, column, backend_data):
        """
        Manages transformations to the backend

        The idea with this (and `column_from_backend`) is that the transformations to
        and from the backend are mostly determined by the column type - integer, string,
        date, etc...  However, there are cases where these are also backend specific: a datetime
        column may be serialized different ways for different databases, a JSON column must be
        serialized for a database but won't be serialized for an API call, etc...  Therefore
        we mostly just let the column handle this, but we want the backend to be in charge
        in case it needs to make changes.
        """
        return column.to_backend(backend_data)
