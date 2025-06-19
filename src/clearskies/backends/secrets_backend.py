from typing import Any, override

import clearskies
from clearskies import parameters_to_properties
from clearskies.autodoc.schema import Integer as AutoDocInteger
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.autodoc.schema import String as AutoDocString
from clearskies.backends.backend import Backend
from clearskies.di import InjectableProperties, inject
from clearskies.functional import routing, string


class SecretsBackend(Backend):
    """
    Fetch and store data from a secret provider.

    ## Installing Dependencies

    Clearskies uses Akeyless by default to manage the secrets.
    This is not installed by default, but is a named extra that you can install when needed via:

    ```bash
    pip install clear-skies[secrets]
    ```
    """

    """The secrets instance."""
    secrets = inject.Secrets()

    can_count = False

    def __init__(self):
        pass

    def check_query(self, query: clearskies.query.Query) -> None:
        if not query.conditions:
            raise KeyError(f"You must search by an id when using the secrets backend.")

    @override
    def update(self, id: str, data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        """Update the record with the given id with the information from the data dictionary."""
        folder_path = self._make_folder_path(model, id)
        for key, value in data.items():
            if key == model.id_column_name:
                continue
            self.secrets.update(f"{folder_path}{key}", value)

        # and now query again to fetch the updated record.
        return self.records(
            clearskies.query.Query(
                model.__class__, conditions=[clearskies.query.Condition(f"{model.id_column_name}={id}")]
            )
        )[0]

    def create(self, data, model):
        if not model.id_column_name in data:
            raise ValueError(
                f"You must provide '{model.id_column_name}' when creating a record with the secrets backend"
            )
        return self.update(data[model.id_column_name], data, model)

    @override
    def delete(self, id: str) -> bool:
        """
        Delete the record with the given id.

        Note that this isn't implemented yet, and always returns True.
        """
        return True

    def records(
        self, query: clearskies.query.Query, next_page_data: dict[str, str | int] | None = None
    ) -> list[dict[str, Any]]:
        """Return a list of records that match the given query configuration."""
        self.check_query(query)
        for condition in query.conditions:
            if condition.operator != "=":
                raise ValueError(
                    f"I'm not very smart and only know how to search with the equals operator, but I received a condition of {condition.parsed}.  If you need to support this, you'll have to extend the ApiBackend and overwrite the build_records_request method."
                )
            if condition.column_name == query.model_class.id_column_name:
                id = condition.values[0]
                break
        if id is None:
            raise ValueError(f"You must search by '{query.model_class.id_column_name}' when using the secrets backend")

        folder_path = self._make_folder_path(query.model_class, id)
        data = {query.model_class.id_column_name: id}
        for path in self.secrets.list_secrets(folder_path):
            data[path[len(folder_path) :]] = self.secrets.get(path)
        return [data]

    def _make_folder_path(self, model, id):
        return model.table_name().rstrip("/") + "/" + id.strip("/") + "/"

    def validate_pagination_kwargs(self, kwargs):
        pass

    def allowed_pagination_keys(self):
        return []

    def documentation_pagination_next_page_response(self, case_mapping):
        return {}

    def documentation_pagination_parameters(self, case_mapping):
        return {}

    def documentation_pagination_next_page_example(self, case_mapping):
        return {}
