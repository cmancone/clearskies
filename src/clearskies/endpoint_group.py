from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Self

import clearskies.configurable
import clearskies.di
import clearskies.end
from clearskies import exceptions
from clearskies.authentication import Authentication, Authorization, Public
from clearskies.endpoint import Endpoint
from clearskies.functional import routing
from clearskies.input_outputs import InputOutput

if TYPE_CHECKING:
    from clearskies import SecurityHeader


class EndpointGroup(
    clearskies.end.End,  # type: ignore
    clearskies.configurable.Configurable,
    clearskies.di.InjectableProperties,
):
    """
    An endpoint group brings endpoints together: it basically handles routing.

    The endpoint group accepts a list of endpoints/endpoint groups and routes requests to them.  You can set a URL for
    the endpoint group, and this becomes a URL prefix for all of the endpoints under it.  Note that all routing is
    greedy, which means you want to put endpoints with more specific URLs first.  Here's an example of how
    you can use them to build a fully functional API that manages both users and companies.  Each individual
    endpoint is defined for the purpose of the example, but note that in practice you could accomplish this same
    thing with much less code by using the RestfulApi endpoint:

    ```python
    import clearskies
    from clearskies.validators import Required, Unique
    from clearskies import columns


    class Company(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = columns.Uuid()
        name = columns.String(
            validators=[
                Required(),
                Unique(),
            ]
        )


    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = columns.Uuid()
        name = columns.String(validators=[Required()])
        username = columns.String(
            validators=[
                Required(),
                Unique(),
            ]
        )
        age = columns.Integer(validators=[Required()])
        created_at = columns.Created()
        updated_at = columns.Updated()
        company_id = columns.BelongsToId(
            Company,
            readable_parent_columns=["id", "name"],
            validators=[Required()],
        )
        company = columns.BelongsToModel("company_id")


    readable_user_column_names = [
        "id",
        "name",
        "username",
        "age",
        "created_at",
        "updated_at",
        "company",
    ]
    writeable_user_column_names = ["name", "username", "age", "company_id"]
    users_api = clearskies.EndpointGroup(
        [
            clearskies.endpoints.Update(
                model_class=User,
                url="/:id",
                readable_column_names=readable_user_column_names,
                writeable_column_names=writeable_user_column_names,
            ),
            clearskies.endpoints.Delete(
                model_class=User,
                url="/:id",
            ),
            clearskies.endpoints.Get(
                model_class=User,
                url="/:id",
                readable_column_names=readable_user_column_names,
            ),
            clearskies.endpoints.Create(
                model_class=User,
                readable_column_names=readable_user_column_names,
                writeable_column_names=writeable_user_column_names,
            ),
            clearskies.endpoints.SimpleSearch(
                model_class=User,
                readable_column_names=readable_user_column_names,
                sortable_column_names=readable_user_column_names,
                searchable_column_names=readable_user_column_names,
                default_sort_column_name="name",
            ),
        ],
        url="users",
    )

    readable_company_column_names = ["id", "name"]
    writeable_company_column_names = ["name"]
    companies_api = clearskies.EndpointGroup(
        [
            clearskies.endpoints.Update(
                model_class=Company,
                url="/:id",
                readable_column_names=readable_company_column_names,
                writeable_column_names=writeable_company_column_names,
            ),
            clearskies.endpoints.Delete(
                model_class=Company,
                url="/:id",
            ),
            clearskies.endpoints.Get(
                model_class=Company,
                url="/:id",
                readable_column_names=readable_company_column_names,
            ),
            clearskies.endpoints.Create(
                model_class=Company,
                readable_column_names=readable_company_column_names,
                writeable_column_names=writeable_company_column_names,
            ),
            clearskies.endpoints.SimpleSearch(
                model_class=Company,
                readable_column_names=readable_company_column_names,
                sortable_column_names=readable_company_column_names,
                searchable_column_names=readable_company_column_names,
                default_sort_column_name="name",
            ),
        ],
        url="companies",
    )

    wsgi = clearskies.contexts.WsgiRef(clearskies.EndpointGroup([users_api, companies_api]))
    wsgi()
    ```

    Usage then works exactly as expected:

    ```bash
    $ curl 'http://localhost:8080/companies' -d '{"name": "Box Store"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "f073ee4d-318d-4e0b-a796-f450c40aa771",
            "name": "Box Store"
        },
        "pagination": {},
        "input_errors": {}
    }

    curl 'http://localhost:8080/users' -d '{"name": "Bob Brown", "username": "bobbrown", "age": 25, "company_id": "f073ee4d-318d-4e0b-a796-f450c40aa771"}'
    curl 'http://localhost:8080/users' -d '{"name": "Jane Doe", "username": "janedoe", "age": 32, "company_id": "f073ee4d-318d-4e0b-a796-f450c40aa771"}'

    $ curl 'http://localhost:8080/users' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "68cbb9e9-689a-4ae0-af77-d60e4cb344f1",
                "name": "Bob Brown",
                "username": "bobbrown",
                "age": 25,
                "created_at": "2025-06-08T10:40:37+00:00",
                "updated_at": "2025-06-08T10:40:37+00:00",
                "company": {
                    "id": "f073ee4d-318d-4e0b-a796-f450c40aa771",
                    "name": "Box Store"
                }
            },
            {
                "id": "e69c4ebf-38b1-40d2-b523-5d58f5befc7b",
                "name": "Jane Doe",
                "username": "janedoe",
                "age": 32,
                "created_at": "2025-06-08T10:41:04+00:00",
                "updated_at": "2025-06-08T10:41:04+00:00",
                "company": {
                    "id": "f073ee4d-318d-4e0b-a796-f450c40aa771",
                    "name": "Box Store"
                }
            }
        ],
        "pagination": {
            "number_results": 2,
            "limit": 50,
            "next_page": {}
        },
        "input_errors": {}
    }

    ```
    """

    """
    The dependency injection container
    """
    di = clearskies.di.inject.Di()
    url = clearskies.configs.String(default="")
    response_headers = clearskies.configs.StringListOrCallable(default=[])
    authentication = clearskies.configs.Authentication(default=Public())
    authorization = clearskies.configs.Authorization(default=Authorization())
    security_headers = clearskies.configs.SecurityHeaders(default=[])
    cors_header: SecurityHeader = None  # type: ignore
    has_cors: bool = False
    endpoints_initialized = False

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        endpoints: list[Endpoint | Self],
        url: str = "",
        response_headers: list[str | Callable[..., list[str]]] = [],
        security_headers: list[SecurityHeader] = [],
        authentication: Authentication = Public(),
        authorization: Authorization = Authorization(),
    ):
        self.finalize_and_validate_configuration()
        for security_header in self.security_headers:
            if not security_header.is_cors:
                continue
            self.cors_header = security_header
            self.has_cors = True
            break

        if not endpoints:
            raise ValueError(
                "An endpoint group must receive a list of endpoints/endpoint groups, but my list of endpoints is empty."
            )
        if not isinstance(endpoints, list):
            raise ValueError(
                f"An endpoint group must receive a list of endpoints/endpoint groups, but instead of a list I found an object of type '{endpoints.__class__.__name__}'"
            )
        for index, endpoint in enumerate(endpoints):
            if not isinstance(endpoint, Endpoint) and not isinstance(endpoint, self.__class__):
                raise ValueError(
                    f"An endpoint group must receive a list of endpoints/endpoint groups, but item #{index + 1} was neither an endpoint nor an endpoint group, but an object of type '{endpoints.__class__.__name__}'"
                )
            if self.url.strip("/"):
                endpoint.add_url_prefix(self.url)

    def matches_request(self, input_output: InputOutput, allow_partial=True) -> bool:
        """Whether or not we can handle an incoming request based on URL and request method."""
        expected_url = self.url.strip("/")
        incoming_url = input_output.get_full_path().strip("/")
        if not expected_url and not incoming_url:
            return True
        (matches, routing_data) = routing.match_route(expected_url, incoming_url, allow_partial=allow_partial)
        return matches

    def populate_routing_data(self, input_output: InputOutput) -> Any:
        # only endpoints (not the endpoint group) can handle this because the endpoint group doesn't have the full url
        return None

    def handle(self, input_output):
        if not self.endpoints_initialized:
            self.endpoints_initialized = True
            for endpoint in self.endpoints:
                endpoint.injectable_properties(self.di)

        has_match = False
        for endpoint in self.endpoints:
            if not endpoint.matches_request(input_output):
                continue
            has_match = True
            break

        if not has_match:
            return self.error(input_output, "Not Found", 404)

        self.add_response_headers(input_output)
        return endpoint(input_output)

    def error(self, input_output: InputOutput, message: str, status_code: int) -> Any:
        """Return a client-side error (e.g. 400)."""
        return self.respond_json(input_output, {"status": "client_error", "error": message}, status_code)
