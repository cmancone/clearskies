from __future__ import annotations

import urllib.parse
from typing import TYPE_CHECKING, Any, Callable

import requests

import clearskies.columns.datetime
import clearskies.columns.json
import clearskies.configs
import clearskies.configurable
import clearskies.model
import clearskies.query
from clearskies import parameters_to_properties
from clearskies.autodoc.schema import Integer as AutoDocInteger
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.autodoc.schema import String as AutoDocString
from clearskies.backends.backend import Backend
from clearskies.di import InjectableProperties, inject
from clearskies.functional import routing, string

if TYPE_CHECKING:
    import clearskies.column


class ApiBackend(clearskies.configurable.Configurable, Backend, InjectableProperties):
    """
    Fetch and store data from an API endpoint.

    The ApiBackend gives developers a way to quickly build SDKs to connect a clearskies applications
    to arbitrary API endpoints.  The backend has some built in flexibility to make it easy to connect it to
    **most** APIs, as well as behavioral hooks so that you can override small sections of the logic to accommodate
    APIs that don't work in the expected way.  This allows you to interact with APIs using the standard model
    methods, just like every other backend, and also means that you can attach such models to endpoints to
    quickly enable all kinds of pre-defined behaviors.

    ## Usage

    Configuring the API backend is pretty easy:

     1. Provide the `base_url` to the constructor, or extend it and set it in the `__init__` for the new backend.
     2. Provide a `clearskies.authentication.Authentication` object, assuming it isn't a public API.
     3. Match your model class name to the path of the API (or set `model.destination_name()` appropriately)
     4. Use the resulting model like you would any other model!

    It's important to understand how the Api Backend will map queries and saves to the API in question.  The rules
    are fairly simple:

      1. The API backend only supports searching with the equals operator (e.g. `models.where("column=value")`).
      2. To specify routing parameters, use the `{parameter_name}` or `:parameter_name` syntax in either the url
         or in the destination name of your model.  In order to query the model, you then **must** provide a value
         for any routing parameters, using a matching search condition: (e.g.
         `models.where("routing_parameter_name=value")`)
      3. Any search clauses that don't correspond to routing parameters will be translated into query parameters.
         So, if your destination_name is `https://example.com/:categoy_id/products` and you executed a
         model query: `models.where("category_id=10").where("on_sale=1")` then this would result in fetching
         a URL of `https://example.com/10/products?on_sale=1`
      4. When you specifically search on the id column for the model, the id will be appended to the end
         of the URL rather than as a query parameter.  So, with a destination name of `https://example.com/products`,
         querying for `models.find("id=10")` will result in fetching `https://example.com/products/10`.
      5. Delete and Update operations will similarly append the id to the URL, and also set the appropriate
         response method (e.g. `DELETE` or `PATCH` by default).
      6. When processing the response, the backend will attempt to automatically discover the results by looking
         for dictionaries that contain the expected column names (as determined from the model schema and the mapping
         rules).
      7. The backend will check for a response header called `link` and parse this to find pagination information
         so it can iterate through records.

    NOTE: The API backend doesn't support joins or group_by clauses.  This limitation, as well as the fact that it only
    supports seaching with the equals operator, isn't a limitation in the API backend itself, but simply reflects the behavior
    of most API endoints.  If you want to support an API that has more flexibility (for instance, perhaps it allows for more search
    operations than just `=`), then you can extend the appropritae methods, discussed below, to map a model query to an API request.

    Here's an example of how to use the API Backend to integrate with the Github API:

    ```python
    import clearskies


    class GithubPublicBackend(clearskies.backends.ApiBackend):
        def __init__(
            self,
            # This varies from endpoint to endpoint, so we want to be able to set it for each model
            pagination_parameter_name: str = "since",
        ):
            # these are fixed for all gitlab API parameters, so there's no need to make them setable
            # from the constructor
            self.base_url = "https://api.github.com"
            self.limit_parameter_name = "per_page"
            self.pagination_parameter_name = pagination_parameter_name
            self.finalize_and_validate_configuration()


    class UserRepo(clearskies.Model):
        # Corresponding API Docs: https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#list-repositories-for-a-user
        id_column_name = "full_name"
        backend = GithubPublicBackend(pagination_parameter_name="page")

        @classmethod
        def destination_name(cls) -> str:
            return "users/:login/repos"

        id = clearskies.columns.Integer()
        full_name = clearskies.columns.String()
        type = clearskies.columns.Select(["all", "owner", "member"])
        url = clearskies.columns.String()
        html_url = clearskies.columns.String()
        created_at = clearskies.columns.Datetime()
        updated_at = clearskies.columns.Datetime()

        # The API endpoint won't return "login" (e.g. username), so it may not seem like a column, but we need to search by it
        # because it's a URL parameter for this API endpoint.  Clearskies uses strict validation and won't let us search by
        # a column that doesn't exist in the model: therefore, we have to add the login column.
        login = clearskies.columns.String(is_searchable=True, is_readable=False)

        # The API endpoint let's us sort by `created`/`updated`.  Note that the names of the columns (based on the data returned
        # by the API endpoint) are `created_at`/`updated_at`.  As above, clearskies strictly validates data, so we need columns
        # named created/updated so that we can sort by them.  We can set some flags to (hopefully) avoid confusion
        updated = clearskies.columns.Datetime(
            is_searchable=False, is_readable=False, is_writeable=False
        )
        created = clearskies.columns.Datetime(
            is_searchable=False, is_readable=False, is_writeable=False
        )


    class User(clearskies.Model):
        # Corresponding API docs: https://docs.github.com/en/rest/users/users?apiVersion=2022-11-28#list-users

        # github has two columns that are both effecitvely id columns: id and login.
        # We use the login column for id_column_name because that is the column that gets
        # used in the API to fetch an individual record
        id_column_name = "login"
        backend = GithubPublicBackend()

        id = clearskies.columns.Integer()
        login = clearskies.columns.String()
        gravatar_id = clearskies.columns.String()
        avatar_url = clearskies.columns.String()
        html_url = clearskies.columns.String()
        repos_url = clearskies.columns.String()

        # We can hook up relationships between models just like we would if we were using an SQL-like
        # database.  The whole point of the backend system is that the model queries work regardless of
        # backend, so clearskies can issue API calls to fetch related records just like it would be able
        # to fetch children from a related database table.
        repos = clearskies.columns.HasMany(
            UserRepo,
            foreign_column_name="login",
            readable_child_columns=["id", "full_name", "html_url"],
        )


    def fetch_user(users: User, user_repos: UserRepo):
        # If we execute this models query:
        some_repos = (
            user_repos.where("login=cmancone")
            .sort_by("created", "desc")
            .where("type=owner")
            .pagination(page=2)
            .limit(5)
        )
        # the API backend will fetch this url:
        # https://api.github.com/users/cmancone/repos?type=owner&sort=created&direction=desc&per_page=5&page=2
        # and we can use the results like always
        repo_names = [repo.full_name for repo in some_repos]

        # For the below case, the backend will fetch this url:
        # https://api.github.com/users/cmancone
        # in addition, the readable column names on the callable endpoint includes "repos", which references our has_many
        # column.  This means that when converting the user model to JSON, it will also grab a page of repositories for that user.
        # To do that, it will fetch this URL:
        # https://api.github.com/users/cmancone/repos
        return users.find("login=cmancone")


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Callable(
            fetch_user,
            model_class=User,
            readable_column_names=["id", "login", "html_url", "repos"],
        ),
        classes=[User, UserRepo],
    )

    if __name__ == "__main__":
        wsgi()
    ```

    The following example demonstrates how models using this backend can be used in other clearskies endpoints, just like any
    other model.  Note that the following example is re-using the above models and backend, I have just omitted them for the sake
    of brevity:

    ```python
    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.List(
            model_class=User,
            readable_column_names=["id", "login", "html_url"],
            sortable_column_names=["id"],
            default_sort_column_name=None,
            default_limit=10,
        ),
        classes=[User],
    )

    if __name__ == "__main__":
        wsgi()
    ```

    And if you invoke it:

    ```bash
    $ curl 'http://localhost:8080' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": 1,
                "login": "mojombo",
                "html_url": "https://github.com/mojombo"
            },
            {
                "id": 2,
                "login": "defunkt",
                "html_url": "https://github.com/defunkt"
            },
            {
                "id": 3,
                "login": "pjhyett",
                "html_url": "https://github.com/pjhyett"
            },
            {
                "id": 4,
                "login": "wycats",
                "html_url": "https://github.com/wycats"
            },
            {
                "id": 5,
                "login": "ezmobius",
                "html_url": "https://github.com/ezmobius"
            },
            {
                "id": 6,
                "login": "ivey",
                "html_url": "https://github.com/ivey"
            },
            {
                "id": 7,
                "login": "evanphx",
                "html_url": "https://github.com/evanphx"
            },
            {
                "id": 17,
                "login": "vanpelt",
                "html_url": "https://github.com/vanpelt"
            },
            {
                "id": 18,
                "login": "wayneeseguin",
                "html_url": "https://github.com/wayneeseguin"
            },
            {
                "id": 19,
                "login": "brynary",
                "html_url": "https://github.com/brynary"
            }
        ],
        "pagination": {
            "number_results": null,
            "limit": 10,
            "next_page": {
                "since": "19"
            }
        },
        "input_errors": {}
    }
    ```

    In essence, we now have an endpoint that lists results but, instead of pulling its data from a database, it
    makes API calls.  It also tracks pagination as expected, so you can use the data in `pagination.next_page` to
    fetch the next set of results, just as you would if this were backed by a database, e.g.:

    ```bash
    $ curl http://localhost:8080?since=19
    ```

    ## Mapping from Queries to API calls

    The process of mapping a model query into an API request involves a few different methods which can be
    overwritten to fully control the process.  This is necessary in cases where an API behaves differently
    than expected by the API backend.  This table outlines the method involved and how they are used:

    | Method                           | Description                                                                                           |
    |----------------------------------|-------------------------------------------------------------------------------------------------------|
    | records_url                      | Return the absolute URL to fetch, as well as any columns that were used to fill in routing parameters |
    | records_method                   | Reurn the HTTP request method to use for the API call                                                 |
    | conditions_to_request_parameters | Translate the query conditions into URL fragments, query parameters, or JSON body parameters          |
    | pagination_to_request_parameters | Translate the pagination data into URL fragments, query parameters, or JSON body parameters           |
    | sorts_to_request_parameters      | Translate the sort directive(s) into URL fragments, query parameters, or JSON body parameters         |
    | map_records_response             | Take the response from the API and return a list of dictionaries with the resulting records           |

    In short, the details of the query are stored in a clearskies.query.Query object which is passed around to these
    various methods.  They use that information to adjust the URL, add query parameters, or add parameters into the
    JSON body.  The API Backend will then execute an API call with those final details, and use the map_record_response
    method to pull the returned records out of the response from the API endpoint.

    """

    can_count = False

    """
    The Base URL for the requests - will be prepended to the destination_name() from the model.

    Note: this is treated as a 'folder' path: if set, it becomes the URL prefix and is followed with a '/'
    """
    base_url = clearskies.configs.String(default="")

    """
    A suffix to append to the end of the URL.

    Note: this is treated as a 'folder' path: if set, it becomes the URL suffix and is prefixed with a '/'
    """
    url_suffix = clearskies.configs.String(default="")

    """
    An instance of clearskies.authentication.Authentication that handles authentication to the API.

    The following example is a modification of the Github Backends used above that shows how to setup authentication.
    Github, like many APIs, uses an API key attached to the request via the authorization header.  The SecretBearer
    authentication class in clearskies is designed for this common use case, and pulls the secret key out of either
    an environment variable or the secret manager (I use the former in this case, because it's hard to have a
    self-contained example with a secret manager).  Of course, any authentication method can be attached to your
    API backend - SecretBearer authentication is used here simply because it's a common approach.

    Note that, when used in conjunction with a secret manager, the API Backend and the SecretBearer class will work
    together to check for a new secret in the event of an authentication failure from the API endpoint (specifically,
    a 401 error).  This allows you to automate credential rotation: create a new API key, put it in the secret manager,
    and then revoke the old API key.  The next time an API call is made, the SecretBearer will provide the old key from
    it's cache and the request will fail.  The API backend will detect this and try the request again, but this time
    will tell the SecretBearer class to refresh it's cache with a fresh copy of the key from the secrets manager.
    Therefore, as long as you put the new key in your secret manager **before** disabling the old key, this second
    request will succeed and the service will continue to operate successfully with only a slight delay in response time
    caused by refreshing the cache.

    ```python
    import clearskies

    class GithubBackend(clearskies.backends.ApiBackend):
        def __init__(
            self,
            pagination_parameter_name: str = "page",
            authentication: clearskies.authentication.Authentication | None = None,
        ):
            self.base_url = "https://api.github.com"
            self.limit_parameter_name = "per_page"
            self.pagination_parameter_name = pagination_parameter_name
            self.authentication = clearskies.authentication.SecretBearer(
                environment_key="GITHUB_API_KEY",
                header_prefix="Bearer ", # Because github expects a header of 'Authorization: Bearer API_KEY'
            )
            self.finalize_and_validate_configuration()

    class Repo(clearskies.Model):
        id_column_name = "login"
        backend = GithubBackend()

        @classmethod
        def destination_name(cls):
            return "/user/repos"

        id = clearskies.columns.Integer()
        name = clearskies.columns.String()
        full_name = clearskies.columns.String()
        html_url = clearskies.columns.String()
        visibility = clearskies.columns.Select(["all", "public", "private"])

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.List(
            model_class=Repo,
            readable_column_names=["id", "name", "full_name", "html_url"],
            sortable_column_names=["full_name"],
            default_sort_column_name="full_name",
            default_limit=10,
            where=["visibility=private"],
        ),
        classes=[Repo],
    )

    if __name__ == "__main__":
        wsgi()

    ```
    """
    authentication = clearskies.configs.Authentication(default=None)

    """
    A dictionary of headers to attach to all outgoing API requests
    """
    headers = clearskies.configs.StringDict(default={})

    """
    The casing used in the model (snake_case, camelCase, TitleCase)

    This is used in conjunction with api_casing to tell the processing layer when you and the API are using
    different casing standards.  The API backend will then automatically covnert the casing style of the API
    to match your model.  This can be helpful when you have a standard naming convention in your own code which
    some external API doesn't follow, that way you can at least standardize things in your code.  In the following
    example, these parameters are used to convert from the snake_casing native to the Github API into the
    TitleCasing used in the model class:

    ```python
    import clearskies

    class User(clearskies.Model):
        id_column_name = "login"
        backend = clearskies.backends.ApiBackend(
            base_url="https://api.github.com",
            limit_parameter_name="per_page",
            pagination_parameter_name="since",
            model_casing="TitleCase",
            api_casing="snake_case",
        )

        Id = clearskies.columns.Integer()
        Login = clearskies.columns.String()
        GravatarId = clearskies.columns.String()
        AvatarUrl = clearskies.columns.String()
        HtmlUrl = clearskies.columns.String()
        ReposUrl = clearskies.columns.String()

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.List(
            model_class=User,
            readable_column_names=["Login", "AvatarUrl", "HtmlUrl", "ReposUrl"],
            sortable_column_names=["Id"],
            default_sort_column_name=None,
            default_limit=2,
            internal_casing="TitleCase",
            external_casing="TitleCase",
        ),
        classes=[User],
    )

    if __name__ == "__main__":
        wsgi()
    ```

    and when executed:

    ```bash
    $ curl http://localhost:8080 | jq
    {
        "Status": "Success",
        "Error": "",
        "Data": [
            {
                "Login": "mojombo",
                "AvatarUrl": "https://avatars.githubusercontent.com/u/1?v=4",
                "HtmlUrl": "https://github.com/mojombo",
                "ReposUrl": "https://api.github.com/users/mojombo/repos"
            },
            {
                "Login": "defunkt",
                "AvatarUrl": "https://avatars.githubusercontent.com/u/2?v=4",
                "HtmlUrl": "https://github.com/defunkt",
                "ReposUrl": "https://api.github.com/users/defunkt/repos"
            }
        ],
        "Pagination": {
            "NumberResults": null,
            "Limit": 2,
            "NextPage": {
                "Since": "2"
            }
        },
        "InputErrors": {}
    }
    ```
    """
    model_casing = clearskies.configs.Select(["snake_case", "camelCase", "TitleCase"], default="snake_case")

    """
    The casing used by the API response (snake_case, camelCase, TitleCase)

    See model_casing for details and usage.
    """
    api_casing = clearskies.configs.Select(["snake_case", "camelCase", "TitleCase"], default="snake_case")

    """
    A mapping from the data keys returned by the API to the data keys expected in the model

    This comes into play when you want your model columns to use different names than what is returned by the
    API itself.  Provide a dictionary where the key is the name of a piece of data from the API, and the value
    is the name of the column in the model.  The API Backend will use this to match the API data to your model.
    In the example below, `html_url` from the API has been mapped to `profile_url` in the model:

    ```python
    import clearskies

    class User(clearskies.Model):
        id_column_name = "login"
        backend = clearskies.backends.ApiBackend(
            base_url="https://api.github.com",
            limit_parameter_name="per_page",
            pagination_parameter_name="since",
            api_to_model_map={"html_url": "profile_url"},
        )

        id = clearskies.columns.Integer()
        login = clearskies.columns.String()
        profile_url = clearskies.columns.String()

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.List(
            model_class=User,
            readable_column_names=["login", "profile_url"],
            sortable_column_names=["id"],
            default_sort_column_name=None,
            default_limit=2,
        ),
        classes=[User],
    )

    if __name__ == "__main__":
        wsgi()
    ```

    And if you invoke it:

    ```bash
    $ curl http://localhost:8080 | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "login": "mojombo",
                "profile_url": "https://github.com/mojombo"
            },
            {
                "login": "defunkt",
                "profile_url": "https://github.com/defunkt"
            }
        ],
        "pagination": {
            "number_results": null,
            "limit": 2,
            "next_page": {
                "since": "2"
            }
        },
        "input_errors": {}
    }
    ```
    """
    api_to_model_map = clearskies.configs.StringDict(default={})

    """
    The name of the pagination parameter
    """
    pagination_parameter_name = clearskies.configs.String(default="start")

    """
    The expected 'type' of the pagination parameter: must be either 'int' or 'str'

    Note: this is set as a literal string, not as a type.
    """
    pagination_parameter_type = clearskies.configs.Select(["int", "str"], default="str")

    """
    The name of the parameter that sets the number of records per page (if empty, setting the page size will not be allowed)
    """
    limit_parameter_name = clearskies.configs.String(default="limit")

    """
    The requests instance.
    """
    requests = inject.Requests()

    """
    The dependency injection container (so we can pass it along to the Authentication object)
    """
    di = inject.Di()

    _auth_injected = False
    _response_to_model_map: dict[str, str] = None  # type: ignore

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        base_url: str,
        authentication: clearskies.authentication.Authentication | None = None,
        model_casing: str = "snake_case",
        api_casing: str = "snake_case",
        api_to_model_map: dict[str, str] = {},
        pagination_parameter_name: str = "start",
        pagination_parameter_type: str = "str",
        limit_parameter_name: str = "limit",
    ):
        self.finalize_and_validate_configuration()

    def finalize_url(self, url: str, available_routing_data: dict[str, str], operation: str) -> tuple[str, list[str]]:
        """
        Given a URL, this will append the base URL, fill in any routing data, and also return any used routing parameters.

        For example, consider a base URL of `/my/api/{record_id}/:other_id` and then this is called as so:

        ```python
        (url, used_routing_parameters) = api_backend.finalize_url(
            "entries",
            {
                "record_id": "1-2-3-4",
                "other_id": "a-s-d-f",
                "more_things": "qwerty",
            },
        )
        ```

        The returned url would be `/my/api/1-2-3-4/a-s-d-f/entries`, and used_routing_parameters would be ["record_id", "other_id"].
        The latter is returned so you can understand what parameters were absorbed into the URL.  Often, when some piece of data
        becomes a routing parameter, it needs to be ignored in the rest of the request.  `used_routing_parameters` helps with that.
        """
        base_url = self.base_url.strip("/") + "/" if self.base_url.strip("/") else ""
        url_suffix = "/" + self.url_suffix.strip("/") if self.url_suffix.strip("/") else ""
        url = base_url + url + url_suffix
        routing_parameters = routing.extract_url_parameter_name_map(url)
        if not routing_parameters:
            return (url, [])

        parts = url.split("/")
        used_routing_parameters = []
        for parameter_name, index in routing_parameters.items():
            if parameter_name not in available_routing_data:
                a = "an" if operation == "update" else "a"
                raise ValueError(
                    f"""Failed to generate URL while building {a} {operation} request!  Url {url} hsa a routing parameter named
                    {parameter_name} that I couldn't fill in from the request details.  When fetching records, this should be
                    provided by adding an equals condition to the model, e.g. `model.where("{parameter_name}=some_value")`.
                    When creating/updating a record, this should be provided in the save data, e.g.:
                    `model.save({{"{parameter_name}": "some_value"}})`
                    """
                )
            if available_routing_data[parameter_name].__class__ not in [str, int]:
                parameter_type = available_routing_data[parameter_name].__class__.__name__
                raise ValueError(
                    f"I was filling in a routing parameter named {parameter_name} but the value I was given has a type of {parameter_type}.  Routing parameters can only be strings or integers."
                )
            parts[index] = available_routing_data[parameter_name]
            used_routing_parameters.append(parameter_name)
        return ("/".join(parts), used_routing_parameters)

    def finalize_url_from_data(self, url: str, data: dict[str, Any], operation: str) -> tuple[str, list[str]]:
        """
        Create the final URL using a data dictionary to fill in any URL parameters.

        See finalize_url for more details about the return value
        """
        return self.finalize_url(url, data, operation)

    def finalize_url_from_query(self, query: clearskies.query.Query, operation: str) -> tuple[str, list[str]]:
        """
        Create the URL using a query to fill in any URL parameters.

        See finalize_url for more details about the return value
        """
        available_routing_data = {}
        for condition in query.conditions:
            if condition.operator != "=":
                continue
            available_routing_data[condition.column_name] = condition.values[0]
        return self.finalize_url(query.model_class.destination_name(), available_routing_data, operation)

    def create_url(self, data: dict[str, Any], model: clearskies.model.Model) -> tuple[str, list[str]]:
        """
        Calculate the URL to use for a create requst.  Also, return the list of ay data parameters used to construct the URL.

        See finalize_url for more details on the return value.
        """
        return self.finalize_url_from_data(model.destination_name(), data, "create")

    def create_method(self, data: dict[str, Any], model: clearskies.model.Model) -> str:
        """Return the request method to use with a create request."""
        return "POST"

    def records_url(self, query: clearskies.query.Query) -> tuple[str, list[str]]:
        """
        Calculate the URL to use for a records request.  Also, return the list of any query parameters used to construct the URL.

        See finalize_url for more details on the return value.
        """
        return self.finalize_url_from_query(query, "records")

    def records_method(self, query: clearskies.query.Query) -> str:
        """Return the request method to use when fetching records from the API."""
        return "GET"

    def count_url(self, query: clearskies.query.Query) -> tuple[str, list[str]]:
        """
        Calculate the URL to use for a request to get a record count..  Also, return the list of any query parameters used to construct the URL.

        See finalize_url for more details on the return value.
        """
        return self.records_url(query)

    def count_method(self, query: clearskies.query.Query) -> str:
        """Return the request method to use when making a request for a record count."""
        return self.records_method(query)

    def delete_url(self, id: int | str, model: clearskies.model.Model) -> tuple[str, list[str]]:
        """
        Calculate the URL to use for a delete request.  Also, return the list of any query parameters used to construct the URL.

        See finalize_url for more details on the return value.
        """
        model_base_url = model.destination_name().strip("/") + "/" if model.destination_name() else ""
        return self.finalize_url_from_data(f"{model_base_url}{id}", model.get_raw_data(), "delete")

    def delete_method(self, id: int | str, model: clearskies.model.Model) -> str:
        """Return the request method to use when deleting records via the API."""
        return "DELETE"

    def update_url(self, id: int | str, data: dict[str, Any], model: clearskies.model.Model) -> tuple[str, list[str]]:
        """
        Calculate the URL to use for an update request.  Also, return the list of any query parameters used to construct the URL.

        See finalize_url for more details on the return value.
        """
        model_base_url = model.destination_name().strip("/") + "/" if model.destination_name() else ""
        return self.finalize_url_from_data(f"{model_base_url}{id}", {**model.get_raw_data(), **data}, "update")

    def update_method(self, id: int | str, data: dict[str, Any], model: clearskies.model.Model) -> str:
        """Return the request method to use for an update request."""
        return "PATCH"

    def update(self, id: int | str, data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        """Update a record."""
        data = {**data}
        (url, used_routing_parameters) = self.update_url(id, data, model)
        request_method = self.update_method(id, data, model)
        for parameter in used_routing_parameters:
            del data[parameter]

        response = self.execute_request(url, request_method, json=data)
        json_response = response.json() if response.content else {}
        new_record = {**model.get_raw_data(), **data}
        if response.content:
            new_record = {**new_record, **self.map_update_response(response.json(), model)}
        return new_record

    def map_update_response(self, response_data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        """
        Take the response from the API endpoint for an update request and figure out where the data lives/return it to build a new model.

        See self.map_record_response for goals/motiviation
        """
        return self.map_record_response(response_data, model.get_columns(), "update")

    def create(self, data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        """Create a record."""
        data = {**data}
        (url, used_routing_parameters) = self.create_url(data, model)
        request_method = self.create_method(data, model)
        for parameter in used_routing_parameters:
            del data[parameter]

        response = self.execute_request(url, request_method, json=data, headers=self.headers)
        json_response = response.json() if response.content else {}
        if response.content:
            return self.map_create_response(response.json(), model)
        return {}

    def map_create_response(self, response_data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        return self.map_record_response(response_data, model.get_columns(), "create")

    def delete(self, id: int | str, model: clearskies.model.Model) -> bool:
        (url, used_routing_parameters) = self.delete_url(id, model)
        request_method = self.delete_method(id, model)

        response = self.execute_request(url, request_method)
        return True

    def records(
        self, query: clearskies.query.Query, next_page_data: dict[str, str | int] | None = None
    ) -> list[dict[str, Any]]:
        self.check_query(query)
        (url, method, body, headers) = self.build_records_request(query)
        response = self.execute_request(url, method, json=body, headers=headers)
        records = self.map_records_response(response.json(), query)
        if isinstance(next_page_data, dict):
            self.set_next_page_data_from_response(next_page_data, query, response)
        return records

    def build_records_request(self, query: clearskies.query.Query) -> tuple[str, str, dict[str, Any], dict[str, str]]:
        (url, used_routing_parameters) = self.records_url(query)

        (condition_route_id, condition_url_parameters, condition_body_parameters) = (
            self.conditions_to_request_parameters(query, used_routing_parameters)
        )
        (pagination_url_parameters, pagination_body_parameters) = self.pagination_to_request_parameters(query)
        (sort_url_parameters, sort_body_parameters) = self.sorts_to_request_parameters(query)

        url_parameters = {
            **condition_url_parameters,
            **pagination_url_parameters,
            **sort_url_parameters,
        }

        body_parameters = {
            **condition_body_parameters,
            **pagination_body_parameters,
            **sort_body_parameters,
        }

        if condition_route_id:
            url = url.rstrip("/") + "/" + condition_route_id
        if url_parameters:
            url = url + "?" + urllib.parse.urlencode(url_parameters)

        return (
            url,
            self.records_method(query),
            body_parameters,
            {},
        )

    def conditions_to_request_parameters(
        self, query: clearskies.query.Query, used_routing_parameters: list[str]
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        route_id = ""

        url_parameters = {}
        for condition in query.conditions:
            if condition.column_name in used_routing_parameters:
                continue
            if condition.operator != "=":
                raise ValueError(
                    f"I'm not very smart and only know how to search with the equals operator, but I received a condition of {condition.parsed}.  If you need to support this, you'll have to extend the ApiBackend and overwrite the build_records_request method."
                )
            if condition.column_name == query.model_class.id_column_name:
                route_id = condition.values[0]
                continue
            url_parameters[condition.column_name] = condition.values[0]

        return (route_id, url_parameters, {})

    def pagination_to_request_parameters(self, query: clearskies.query.Query) -> tuple[dict[str, str], dict[str, Any]]:
        url_parameters = {}
        if query.limit:
            if not self.limit_parameter_name:
                raise ValueError(
                    "The records query attempted to change the limit (the number of results per page) but the backend does not support it.  If it actually does support this, then set an appropriate value for backend.limit_parameter_name"
                )
            url_parameters[self.limit_parameter_name] = str(query.limit)

        if query.pagination.get(self.pagination_parameter_name):
            url_parameters[self.pagination_parameter_name] = str(query.pagination.get(self.pagination_parameter_name))

        return (url_parameters, {})

    def sorts_to_request_parameters(self, query: clearskies.query.Query) -> tuple[dict[str, str], dict[str, Any]]:
        if not query.sorts:
            return ({}, {})

        if len(query.sorts) > 1:
            raise ValueError(
                "I received a query with two sort directives, but I can only handle one.  Sorry!  If you need o support two sort directions, you'll have to extend the ApiBackend and overwrite the build_records_request method."
            )

        return (
            {"sort": query.sorts[0].column_name, "direction": query.sorts[0].direction.lower()},
            {},
        )

    def map_records_response(
        self, response_data: Any, query: clearskies.query.Query, query_data: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Take the response from an API endpoint that returns a list of records and find the actual list of records."""
        columns = query.model_class.get_columns()
        # turn all of our conditions into record data and inject these into the results.  We do this to keep around
        # any query parameters.  This is especially important for any URL parameters, wihch aren't always returned in
        # the data, but which we are likely to need again if we go to update/delete the record.
        if query_data is None:
            query_data = {}
            for condition in query.conditions:
                if condition.operator != "=":
                    continue
                query_data[condition.column_name] = condition.values[0]

        # if our response is actually a list, then presumably the problem is solved.  If the response is a list
        # and the individual items aren't model results though... well, then I'm very confused
        if isinstance(response_data, list):
            if not response_data:
                return []
            if not self.check_dict_and_map_to_model(response_data[0], columns, query_data):
                raise ValueError(
                    f"The response from a records request returned a list, but the records in the list didn't look anything like the model class.  Please check your model class and mapping settings in the API Backend.  If those are correct, then you'll have to override the map_records_response method, because the API you are interacting with is returning data in an unexpected way that I can't automatically figure out."
                )
            return [self.check_dict_and_map_to_model(record, columns, query_data) for record in response_data]  # type: ignore

        if not isinstance(response_data, dict):
            raise ValueError(
                f"The response from a records request returned a variable of type {response_data.__class__.__name__}, which is just confusing.  To do automatic introspection, I need a list or a dictionary.  I'm afraid you'll have to extend the API backend and override the map_record_response method to deal with this."
            )

        for key, value in response_data.items():
            if not isinstance(value, list):
                continue
            return self.map_records_response(value, query, query_data)

        # a records request may only return a single record, so before we fail, let's check for that
        record = self.check_dict_and_map_to_model(response_data, columns, query_data)
        if record is not None:
            return [record]

        raise ValueError(
            "The response from a records request returned a dictionary, but none of the items in the dictionary was a list, so I don't know where to find the records.  I only ever check one level deep in dictionaries.  I'm afraid you'll have to extend the API backend and override the map_records_response method to deal with this."
        )

    def map_record_response(
        self, response_data: dict[str, Any], columns: dict[str, clearskies.column.Column], operation: str
    ) -> dict[str, Any]:
        """
        Take the response from an API endpoint that returns a single record (typically update and create requests) and return the data for a new model.

        The goal of this method is to try to use the model schema to automatically understand the response from the
        the API endpoint.  The goal is for the backend to work out-of-the-box with most APIs.  In general, it works
        by iterating over the response, looking for a dictionary with keys that match the expected model columns.

        Occassionally the automatic introspection may not be able to make sense of the response from an API
        endoint.  If this happens, you have to make a new API backend, override the map_record_response method
        to manage the mapping yourself, and then attach this new backend to your models.
        """
        an = "a" if operation == "create" else "an"
        if not isinstance(response_data, dict):
            raise ValueError(
                f"The response from {an} {operation} request returned a variable of type {response_data.__class__.__name__}, which is just confusing.  To do automatic introspection, I need a dictionary.  I'm afraid you'll have to build your own API backend and override the map_record_response method to deal with this."
            )

        response = self.check_dict_and_map_to_model(response_data, columns)
        if response is None:
            raise ValueError(
                f"I was not able to automatically interpret the response from {an} {operation} request.  This could be a sign of a response that is structured in a very unusual way, or may be a sign that the casing settings and/or columns on your model to properly reflect the API response.  For the former, you will hvae to build your own API backend and override the map_record_response to deal with this."
            )

        return response

    def check_dict_and_map_to_model(
        self,
        response_data: dict[str, Any],
        columns: dict[str, clearskies.column.Column],
        query_data: dict[str, Any] = {},
    ) -> dict[str, Any] | None:
        """
        Check a dictionary in the response to decide if it contains the data for a record.

        If not, it will search the keys for something that looks like a record.
        """
        # first let's get a coherent map of expected-key-names in the response to model names
        response_to_model_map = self.build_response_to_model_map(columns)

        # and now we can see if that appears to be what we have
        response_keys = set(response_data.keys())
        map_keys = set(response_to_model_map.keys())
        matching = response_keys.intersection(map_keys)

        # if nothing matches then clearly this isn't what we're looking for: repeat on all the children
        if not matching:
            for key, value in response_data.items():
                if not isinstance(value, dict):
                    continue
                mapped = self.check_dict_and_map_to_model(value, columns)
                if mapped:
                    return {**query_data, **mapped}

            # no match anywhere :(
            return None

        # we may need to be smarter about whether or not we think we found a match, but for now let's
        # ignore that possibility.  If any columns match between the keys in our response dictionary and
        # the keys that we are expecting to find data in, then just assume that we have found a record.
        mapped = {response_to_model_map[key]: response_data[key] for key in matching}

        # finally, move over anything not mentioned in the map
        for key in response_keys.difference(map_keys):
            mapped[string.swap_casing(key, self.api_casing, self.model_casing)] = response_data[key]

        return {**query_data, **mapped}

    def build_response_to_model_map(self, columns: dict[str, clearskies.column.Column]) -> dict[str, str]:
        if self._response_to_model_map is not None:
            return self._response_to_model_map

        self._response_to_model_map = {}
        for column_name in columns:
            self._response_to_model_map[string.swap_casing(column_name, self.model_casing, self.api_casing)] = (
                column_name
            )
        self._response_to_model_map = {**self._response_to_model_map, **self.api_to_model_map}

        return self._response_to_model_map

    def set_next_page_data_from_response(
        self,
        next_page_data: dict[str, Any],
        query: clearskies.query.Query,
        response: requests.Response,  # type: ignore
    ) -> None:
        """
        Update the next_page_data dictionary with the appropriate data needed to fetch the next page of records.

        This method has a very important job, which is to inform clearskies about how to make another API call to fetch the next
        page of records.  The way this happens is by updating the `next_page_data` dictionary in place with whatever pagination
        information is necessary.  Note that this relies on next_page_data being passed by reference, hence the need to update
        it in place.  That means that you can do this:

        ```python
        next_page_data["some_key"] = "some_value"
        ```

        but if you do this:

        ```python
        next_page_data = {"some_key": "some_value"}
        ```

        Then things simply won't work.
        """
        # Different APIs generally have completely different ways of communicating pagination data, but one somewhat common
        # approach is to use a link header, so let's support that in the base class.
        if "link" not in response.headers:
            return
        next_link = [rel for rel in response.headers["link"].split(",") if 'rel="next"' in rel]
        if not next_link:
            return
        parsed_next_link = urllib.parse.urlparse(next_link[0].split(";")[0].strip(" <>"))
        query_parameters = urllib.parse.parse_qs(parsed_next_link.query)
        if self.pagination_parameter_name not in query_parameters:
            raise ValueError(
                f"Configuration error with {self.__class__.__name__}!  I am configured to expect a pagination key of '{self.pagination_parameter_name}.  However, when I was parsing the next link from a response to get the next pagination details, I could not find the designated pagination key.  This likely means that backend.pagination_parameter_name is set to the wrong value.  The link in question was "
                + parsed_next_link.geturl()
            )
        next_page_data[self.pagination_parameter_name] = query_parameters[self.pagination_parameter_name][0]

    def count(self, query: clearskies.query.Query) -> int:
        raise NotImplementedError(
            f"The {self.__class__.__name__} backend does not support count operations, so you can't use the `len` or `bool` function for any models using it."
        )

    def execute_request(
        self,
        url: str,
        method: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        is_retry=False,
    ) -> requests.models.Response:  # type: ignore
        """
        Execute the actual API request and returns the response object.

        We don't directly call the requests library to support retries in the event of failed authentication.  The goal
        is to support short-lived credentials, and our authentication classes denote if they support this feature.  If
        they do, and the requests fails, then we'll ask the authentication method to refresh its credentials and we
        will retry the request.
        """
        if json is None:
            json = {}
        if headers is None:
            headers = {}

        if self.authentication:
            if not self._auth_injected:
                self._auth_injected = True
                if hasattr(self.authentication, "injectable_properties"):
                    self.authentication.injectable_properties(self.di)
            if is_retry:
                self.authentication.clear_credential_cache()
        # the requests library seems to build a slightly different request if you specify the json parameter,
        # even if it is null, and this causes trouble for some picky servers
        if not json:
            response = self.requests.request(
                method,
                url,
                headers=headers,
                auth=self.authentication if self.authentication else None,
            )
        else:
            response = self.requests.request(
                method,
                url,
                headers=headers,
                json=json,
                auth=self.authentication if self.authentication else None,
            )

        if not response.ok:
            if not is_retry and response.status_code == 401:
                return self.execute_request(url, method, json=json, headers=headers, is_retry=True)
            if not response.ok:
                raise ValueError(
                    f"Failed request.  Status code: {response.status_code}, message: "
                    + response.content.decode("utf-8")
                )

        return response

    def check_query(self, query: clearskies.query.Query) -> None:
        for key in ["joins", "group_by", "selects"]:
            if getattr(query, key):
                raise ValueError(f"{self.__class__.__name__} does not support queries with {key}")

        for condition in query.conditions:
            if condition.operator != "=":
                raise ValueError(
                    f"{self.__class__.__name__} only supports searching with the '=' operator, but I found a search with the {condition.operator} operator"
                )

    def validate_pagination_data(self, data: dict[str, Any], case_mapping: Callable) -> str:
        extra_keys = set(data.keys()) - set(self.allowed_pagination_keys())
        if len(extra_keys):
            key_name = case_mapping(self.pagination_parameter_name)
            return "Invalid pagination key(s): '" + "','".join(extra_keys) + f"'.  Only '{key_name}' is allowed"
        if self.pagination_parameter_name not in data:
            key_name = case_mapping(self.pagination_parameter_name)
            return f"You must specify '{key_name}' when setting pagination"
        value = data[self.pagination_parameter_name]
        try:
            if self.pagination_parameter_type == "int":
                converted = int(value)
        except:
            key_name = case_mapping(self.pagination_parameter_name)
            return f"Invalid pagination data: '{key_name}' must be a number"
        return ""

    def allowed_pagination_keys(self) -> list[str]:
        return [self.pagination_parameter_name]

    def documentation_pagination_next_page_response(self, case_mapping: Callable) -> list[Any]:
        if self.pagination_parameter_type == "int":
            return [AutoDocInteger(case_mapping(self.pagination_parameter_name), example=0)]
        else:
            return [AutoDocString(case_mapping(self.pagination_parameter_name), example="")]

    def documentation_pagination_next_page_example(self, case_mapping: Callable) -> dict[str, Any]:
        return {case_mapping(self.pagination_parameter_name): 0 if self.pagination_parameter_type == "int" else ""}

    def documentation_pagination_parameters(self, case_mapping: Callable) -> list[tuple[AutoDocSchema, str]]:
        return [
            (
                AutoDocInteger(
                    case_mapping(self.pagination_parameter_name),
                    example=0 if self.pagination_parameter_type == "int" else "",
                ),
                "The next record",
            )
        ]

    def column_from_backend(self, column: clearskies.column.Column, value: Any) -> Any:
        """We have a couple columns we want to override transformations for."""
        # most importantly, there's no need to transform a JSON column in either direction
        if isinstance(column, clearskies.columns.json.Json):
            return value
        return super().column_from_backend(column, value)

    def column_to_backend(self, column: clearskies.column.Column, backend_data: dict[str, Any]) -> dict[str, Any]:
        """We have a couple columns we want to override transformations for."""
        # most importantly, there's no need to transform a JSON column in either direction
        if isinstance(column, clearskies.columns.json.Json):
            return backend_data
        # also, APIs tend to have a different format for dates than SQL
        if isinstance(column, clearskies.columns.datetime.Datetime) and column.name in backend_data:
            as_date = (
                backend_data[column.name].isoformat()
                if type(backend_data[column.name]) != str
                else backend_data[column.name]
            )
            return {**backend_data, **{column.name: as_date}}
        return column.to_backend(backend_data)
