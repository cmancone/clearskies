from __future__ import annotations

import inspect
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable

import clearskies.configs
import clearskies.exceptions
import clearskies.parameters_to_properties
from clearskies import authentication, autodoc, typing
from clearskies.authentication import Authentication, Authorization, Public
from clearskies.endpoint import Endpoint
from clearskies.endpoint_group import EndpointGroup
from clearskies.endpoints.create import Create
from clearskies.endpoints.delete import Delete
from clearskies.endpoints.get import Get
from clearskies.endpoints.simple_search import SimpleSearch
from clearskies.endpoints.update import Update
from clearskies.functional import string
from clearskies.input_outputs import InputOutput

if TYPE_CHECKING:
    from clearskies import SecurityHeader
    from clearskies.model import Column, Model, Schema


class RestfulApi(EndpointGroup):
    """
    Full CRUD operations for a model.

    This endpoint group sets up all five standard endpoints to manage a model:

     1. Create
     2. Update
     3. Delete
     4. Get
     5. List

    As such, you can set any option for all of the above endpoints.  All five endpoints are enabled by default
    but can be turned off individually.  It's important to understand that the actual API behavior is controlled
    by other endoints.  This endpoint group creates them and routes requests to them.  So, to fully understand
    the behavior of the subsequent Restful API, you have to consult the documentation for the endpoints themselves.

    For routing purposes, the create and list endpoints are reachable via the URL specified for this endpoint group
    and are separated by request method (POST for create by default, GET for list).  The update, delete, and get
    endoints all expect the id to be appended to the base URL, and then are separated by request method
    (PATCH for update, DELETE for delete, and GET for get).  See the example app and calls below:

    ```python
    import clearskies
    from clearskies.validators import Required, Unique
    from clearskies import columns


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


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.RestfulApi(
            url="users",
            model_class=User,
            readable_column_names=["id", "name", "username", "age", "created_at", "updated_at"],
            writeable_column_names=["name", "username", "age"],
            sortable_column_names=["id", "name", "username", "age", "created_at", "updated_at"],
            searchable_column_names=["id", "name", "username", "age", "created_at", "updated_at"],
            default_sort_column_name="name",
        )
    )
    wsgi()
    ```

    Which spins up a fully functional API.  In the below usage examples we create two users, fetch
    one of them, update a user, delete the other, and then list all users.

    ```bash
    $ curl 'http://localhost:8080/users' -d '{"name":"Bob", "username": "bob", "age": 25}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "8bd9c03f-bb0c-41bd-afbc-f9526ded88f4",
            "name": "Bob",
            "username": "bob",
            "age": 25,
            "created_at": "2025-06-10T12:39:35+00:00",
            "updated_at": "2025-06-10T12:39:35+00:00"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/users' -d '{"name":"Alice", "username": "alice", "age": 22}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "16d483c6-0eb1-4104-b07b-32f3d736223f",
            "name": "Alice",
            "username": "alice",
            "age": 22,
            "created_at": "2025-06-10T12:42:59+00:00",
            "updated_at": "2025-06-10T12:42:59+00:00"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/users/8bd9c03f-bb0c-41bd-afbc-f9526ded88f4' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "8bd9c03f-bb0c-41bd-afbc-f9526ded88f4",
            "name": "Bob",
            "username": "bob",
            "age": 25,
            "created_at": "2025-06-10T12:39:35+00:00",
            "updated_at": "2025-06-10T12:39:35+00:00"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/users/16d483c6-0eb1-4104-b07b-32f3d736223f' -d '{"name":"Alice Smith", "age": 23}' -X PATCH | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "16d483c6-0eb1-4104-b07b-32f3d736223f",
            "name": "Alice Smith",
            "username": "alice",
            "age": 23,
            "created_at": "2025-06-10T12:42:59+00:00",
            "updated_at": "2025-06-10T12:45:01+00:00"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/users/8bd9c03f-bb0c-41bd-afbc-f9526ded88f4' -X DELETE | jq
    {
        "status": "success",
        "error": "",
        "data": {},
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/users/' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
            "id": "16d483c6-0eb1-4104-b07b-32f3d736223f",
            "name": "Alice Smith",
            "username": "alice",
            "age": 23,
            "created_at": "2025-06-10T12:42:59+00:00",
            "updated_at": "2025-06-10T12:45:01+00:00"
            }
        ],
        "pagination": {
            "number_results": 1,
            "limit": 50,
            "next_page": {}
        },
        "input_errors": {}
    }
    ```
    """

    """
    The endpoint class to use for managing the create operation.

    This defaults to `clearskies.endpoints.Create`.  To disable the create operation all together,
    set this to None.
    """
    create_endpoint = clearskies.configs.Endpoint(default=Create)

    """
    The endpoint class to use for managing the delete operation.

    This defaults to `clearskies.endpoints.Delete`.  To disable the delete operation all together,
    set this to None.
    """
    delete_endpoint = clearskies.configs.Endpoint(default=Delete)

    """
    The endpoint class to use for managing the update operation.

    This defaults to `clearskies.endpoints.Update`.  To disable the update operation all together,
    set this to None.
    """
    update_endpoint = clearskies.configs.Endpoint(default=Update)

    """
    The endpoint class to use to fetch individual records.

    This defaults to `clearskies.endpoints.Get`.  To disable the get operation all together,
    set this to None.
    """
    get_endpoint = clearskies.configs.Endpoint(default=Get)

    """
    The endpoint class to use to list records.

    This defaults to `clearskies.endpoints.SimpleSearch`.  To disable the list operation all together,
    set this to None.
    """
    list_endpoint = clearskies.configs.Endpoint(default=SimpleSearch)

    """
    The request method(s) to use to route to the create operation.  Default is ["POST"].
    """
    create_request_methods = clearskies.configs.SelectList(
        allowed_values=["GET", "POST", "PUT", "DELETE", "PATCH"], default=["POST"]
    )

    """
    The request method(s) to use to route to the update operation.  Default is ["PATCH"].
    """
    update_request_methods = clearskies.configs.SelectList(
        allowed_values=["GET", "POST", "PUT", "DELETE", "PATCH"], default=["PATCH"]
    )

    """
    The request method(s) to use to route to the delete operation.  Default is ["DELETE"].
    """
    delete_request_methods = clearskies.configs.SelectList(
        allowed_values=["GET", "POST", "PUT", "DELETE", "PATCH"], default=["DELETE"]
    )

    """
    The request method(s) to use to route to the get operation.  Default is ["GET"].
    """
    get_request_methods = clearskies.configs.SelectList(
        allowed_values=["GET", "POST", "PUT", "DELETE", "PATCH"], default=["GET"]
    )

    """
    The request method(s) to use to route to the create operation.  Default is ["GET"].
    """
    list_request_methods = clearskies.configs.SelectList(
        allowed_values=["GET", "POST", "PUT", "DELETE", "PATCH", "QUERY"], default=["GET", "POST", "QUERY"]
    )

    """
    The request method(s) to use to route to the create operation.  Default is ["POST"].
    """
    id_column_name = clearskies.configs.ModelColumn("model_class", default=None)

    """
    The base URL to be used for all the endpoints.
    """
    url = clearskies.configs.String(default="")

    authentication = clearskies.configs.Authentication(default=Public())
    authorization = clearskies.configs.Authorization(default=Authorization())
    output_map = clearskies.configs.Callable(default=None)
    output_schema = clearskies.configs.Schema(default=None)
    model_class = clearskies.configs.ModelClass(default=None)
    readable_column_names = clearskies.configs.ReadableModelColumns("model_class", default=[])
    writeable_column_names = clearskies.configs.WriteableModelColumns("model_class", default=[])
    searchable_column_names = clearskies.configs.SearchableModelColumns("model_class", default=[])
    sortable_column_names = clearskies.configs.ReadableModelColumns("model_class", default=[])
    default_sort_column_name = clearskies.configs.ModelColumn("model_class", required=True)
    default_sort_direction = clearskies.configs.Select(["ASC", "DESC"], default="ASC")
    default_limit = clearskies.configs.Integer(default=50)
    maximum_limit = clearskies.configs.Integer(default=200)
    group_by_column_name = clearskies.configs.ModelColumn("model_class")
    input_validation_callable = clearskies.configs.Callable(default=None)
    include_routing_data_in_request_data = clearskies.configs.Boolean(default=False)
    column_overrides = clearskies.configs.Columns(default={})
    internal_casing = clearskies.configs.Select(["snake_case", "camelCase", "TitleCase"], default="snake_case")
    external_casing = clearskies.configs.Select(["snake_case", "camelCase", "TitleCase"], default="snake_case")
    security_headers = clearskies.configs.SecurityHeaders(default=[])
    description = clearskies.configs.String(default="")
    where = clearskies.configs.Conditions(default=[])
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        model_class: type[Model],
        writeable_column_names: list[str],
        readable_column_names: list[str],
        searchable_column_names: list[str],
        sortable_column_names: list[str],
        default_sort_column_name: str,
        read_only: bool = False,
        create_endpoint: Endpoint | None = Create,
        delete_endpoint: Endpoint | None = Delete,
        update_endpoint: Endpoint | None = Update,
        get_endpoint: Endpoint | None = Get,
        list_endpoint: Endpoint | None = SimpleSearch,
        create_request_methods: list[str] = ["POST"],
        update_request_methods: list[str] = ["PATCH"],
        delete_request_methods: list[str] = ["DELETE"],
        get_request_methods: list[str] = ["GET"],
        list_request_methods: list[str] = ["GET"],
        id_column_name: str = "",
        group_by_column_name: str = "",
        input_validation_callable: Callable | None = None,
        include_routing_data_in_request_data: bool = False,
        url: str = "",
        default_sort_direction: str = "ASC",
        default_limit: int = 50,
        maximum_limit: int = 200,
        request_methods: list[str] = ["POST"],
        response_headers: list[str | Callable[..., list[str]]] = [],
        output_map: Callable[..., dict[str, Any]] | None = None,
        output_schema: Schema | None = None,
        column_overrides: dict[str, Column] = {},
        internal_casing: str = "snake_case",
        external_casing: str = "snake_case",
        security_headers: list[SecurityHeader] = [],
        description: str = "",
        authentication: Authentication = Public(),
        authorization: Authorization = Authorization(),
    ):
        self.finalize_and_validate_configuration()

        id_column_name = id_column_name if id_column_name else model_class.id_column_name

        # figure out which endpoints we actually need
        endpoints_to_build = []
        if not read_only:
            if create_endpoint:
                endpoints_to_build.append(
                    {
                        "class": create_endpoint,
                        "request_methods": create_request_methods,
                    }
                )
            if delete_endpoint:
                endpoints_to_build.append(
                    {
                        "class": delete_endpoint,
                        "request_methods": delete_request_methods,
                        "url_suffix": f"/:{id_column_name}",
                    }
                )
            if update_endpoint:
                endpoints_to_build.append(
                    {
                        "class": update_endpoint,
                        "request_methods": update_request_methods,
                        "url_suffix": f"/:{id_column_name}",
                    }
                )
        if get_endpoint:
            endpoints_to_build.append(
                {
                    "class": get_endpoint,
                    "request_methods": get_request_methods,
                    "url_suffix": f"/:{id_column_name}",
                }
            )
        if list_endpoint:
            endpoints_to_build.append(
                {
                    "class": list_endpoint,
                    "request_methods": list_request_methods,
                }
            )

        # and now build them!  Pass along our own kwargs to the endoints when we build them.  Now, technically, I
        # know what the kwargs are for each endpoint.  However, it would be a lot of duplication to manually
        # instantiate each endpoint and pass along all the kwargs.  So, fetch the list of kwargs from our own
        # __init__ and then compare that with the kwargs of the __init__ for each endpoint and map everything
        # automatically like that.  Then add in the individual config from above.

        # these lines take all of the arguments we were initialized with and dumps it into a dict.  It's the
        # equivalent of combining both *args and **kwargs without using either
        my_args = inspect.getfullargspec(self.__class__)
        local_variables = inspect.currentframe().f_locals  # type: ignore
        available_args = {arg: local_variables[arg] for arg in my_args.args[1:]}

        # we handle this one manually
        del available_args["url"]

        # now loop through the list of endpoints
        endpoints = []
        for endpoint_to_build in endpoints_to_build:
            # grab our class and any pre-defined configs
            endpoint_class = endpoint_to_build["class"]
            url_suffix = endpoint_to_build.get("url_suffix")

            # now get the allowed args out of the init and fill them out with our own.
            endpoint_args = inspect.getfullargspec(endpoint_class)
            nendpoint_args = len(endpoint_args.args)
            nendpoint_kwargs = len(endpoint_args.defaults) if endpoint_args.defaults else 0
            final_args: list[str] = []
            final_kwargs: dict[str, Any] = {}
            for arg in endpoint_args.args[1:]:
                if not available_args.get(arg):
                    continue
                final_kwargs[arg] = available_args[arg]

            if url_suffix:
                final_kwargs["url"] = url_suffix
            final_kwargs["request_methods"] = endpoint_to_build["request_methods"]
            endpoints.append(endpoint_class(*final_args, **final_kwargs))  # type: ignore

        super().__init__(
            endpoints,
            url=url,
            response_headers=response_headers,
            security_headers=security_headers,
            authentication=authentication,
            authorization=authorization,
        )
