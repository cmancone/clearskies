import inspect
from abc import ABC, abstractmethod
from typing import Any, Callable, Type

import clearskies.column
import clearskies.model
import clearskies.query
from clearskies.autodoc.schema import Schema as AutoDocSchema


class Backend(ABC):
    supports_n_plus_one = False
    can_count = True

    @abstractmethod
    def update(self, id: int | str, data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        """Update the record with the given id with the information from the data dictionary."""
        pass

    @abstractmethod
    def create(self, data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        """Create a record with the information from the data dictionary."""
        pass

    @abstractmethod
    def delete(self, id: int | str, model: clearskies.model.Model) -> bool:
        """Delete the record with the given id."""
        pass

    @abstractmethod
    def count(self, query: clearskies.query.Query) -> int:
        """Return the number of records which match the given query configuration."""
        pass

    @abstractmethod
    def records(
        self, query: clearskies.query.Query, next_page_data: dict[str, str | int] | None = None
    ) -> list[dict[str, Any]]:
        """
        Return a list of records that match the given query configuration.

        next_page_data is used to return data to the caller.  Pass in an empty dictionary, and it will be populated
        with the data needed to return the next page of results.  If it is still an empty dictionary when returned,
        then there is no additional data.
        """
        pass

    @abstractmethod
    def validate_pagination_data(self, data: dict[str, Any], case_mapping: Callable[[str], str]) -> str:
        """
        Check if the given dictionary is valid pagination data for the background.

        Return a string with an error message, or an empty string if the data is valid
        """
        pass

    @abstractmethod
    def allowed_pagination_keys(self) -> list[str]:
        """
        Return the list of allowed keys in the pagination kwargs for the backend.

        It must always return keys in snake_case so that the auto casing system can
        adjust on the front-end for consistency.
        """
        pass

    @abstractmethod
    def documentation_pagination_next_page_response(self, case_mapping: Callable) -> list[Any]:
        """
        Return a list of autodoc schema objects.

        It will describe the contents of the `next_page` dictionary
        in the pagination section of the response
        """
        pass

    @abstractmethod
    def documentation_pagination_parameters(self, case_mapping: Callable) -> list[tuple[AutoDocSchema, str]]:
        """
        Return a list of autodoc schema objects describing the allowed input keys to set pagination.

        It should return a list of tuples, with each tuple corresponding to an input key.
        The first element in the tuple should be the schema, and the second should be the description.
        """
        pass

    @abstractmethod
    def documentation_pagination_next_page_example(self, case_mapping: Callable) -> dict[str, Any]:
        """
        Return an example for next page documentation.

        Returns an example (as a simple dictionary) of what the next_page data in the pagination response
        should look like
        """
        pass

    def column_from_backend(self, column: clearskies.column.Column, value: Any) -> Any:
        """
        Manage transformations from the backend.

        The idea with this (and `column_to_backend`) is that the transformations to
        and from the backend are mostly determined by the column type - integer, string,
        date, etc...  However, there are cases where these are also backend specific: a datetime
        column may be serialized different ways for different databases, a JSON column must be
        serialized for a database but won't be serialized for an API call, etc...  Therefore
        we mostly just let the column handle this, but we want the backend to be in charge
        in case it needs to make changes.
        """
        return column.from_backend(value)

    def column_to_backend(self, column: clearskies.column.Column, backend_data: dict[str, Any]) -> dict[str, Any]:
        """
        Manage transformations to the backend.

        The idea with this (and `column_from_backend`) is that the transformations to
        and from the backend are mostly determined by the column type - integer, string,
        date, etc...  However, there are cases where these are also backend specific: a datetime
        column may be serialized different ways for different databases, a JSON column must be
        serialized for a database but won't be serialized for an API call, etc...  Therefore
        we mostly just let the column handle this, but we want the backend to be in charge
        in case it needs to make changes.
        """
        return column.to_backend(backend_data)
