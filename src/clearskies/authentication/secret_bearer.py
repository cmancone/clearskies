import clearskies.configs
import clearskies.di
import clearskies.parameters_to_properties
from clearskies import autodoc
from clearskies.authentication.authentication import Authentication


class SecretBearer(Authentication, clearskies.di.InjectableProperties):
    """
    Secret Bearer performs authentication by checking against a static API key stored in either environment variables or a secret manager.

    This can be used in two different ways:

     1. Attached to an endpoint to enforce authentication
     2. Attached to an API backend to specify how to authenticate to the API endpoint.

    ### Authenticating Endpoints.

    When attached to an endpoint this will enforce authentication.  Clients authenticate themselves by providing the secret value
    via the `authorization` header.  In the following example we configure the secret bearer class to get the secretfrom an
    environment variable which is set in the code itself.  Normally you wouldn't set environment variables like this,
    but it's done here to create a self-contained example that is easy to run:

    ```
    import os
    import clearskies

    os.environ["MY_AUTH_SECRET"] = "SUPERSECRET"

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Callable(
            lambda: {"hello": "world"},
            authentication=clearskies.authentication.SecretBearer(environment_key="MY_AUTH_SECRET"),
        )
    )
    wsgi()
    ```
    We can then call it with and without the authentication header:

    ```
    $ curl 'http://localhost:8080' -H 'Authorization: SUPERSECRET' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "hello": "world"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080' | jq
    {
        "status": "client_error",
        "error": "Not Authenticated",
        "data": [],
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080' -H 'Authorization: NOTTHESECRET' | jq
    {
        "status": "client_error",
        "error": "Not Authenticated",
        "data": [],
        "pagination": {},
        "input_errors": {}
    }
    ```

    ### Authenticating to APIs

    The secret bearer class can also be attached to an API Backend to provide authentication to remote APIs.  To
    demonstrate, here is an example server that expects a secret token in the authorization header:

    ```
    import os
    import clearskies
    from clearskies import columns

    os.environ["MY_SECRET"] = "SUPERSECRET"

    class Widget(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = columns.Uuid()
        name = columns.String()
        category = columns.String()
        cost = columns.Float()
        created_at = columns.Created()
        updated_at = columns.Updated()

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.RestfulApi(
            url="widgets",
            model_class=Widget,
            authentication=clearskies.authentication.SecretBearer(environment_key="MY_SECRET"),
            readable_column_names=['id', 'name', 'category', 'cost', 'created_at', 'updated_at'],
            writeable_column_names=['name', 'category', 'cost'],
            sortable_column_names=['name', 'category', 'cost'],
            searchable_column_names=['id', 'name', 'category', 'cost'],
            default_sort_column_name="name",
        )
    )
    wsgi()
    ```

    Then here is a client app (you can launch the above server and then run this in a new terminal) that
    similarly uses the secret bearer class to authenticate to the server:

    ```
    import os
    import clearskies
    from clearskies import columns

    os.environ["MY_SECRET"] = "SUPERSECRET"

    class Widget(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.ApiBackend(
            base_url="http://localhost:8080",
            authentication=clearskies.authentication.SecretBearer(environment_key="MY_SECRET"),
        )

        id = columns.String()
        name = columns.String()
        category = columns.String()
        cost = columns.Float()
        created_at = columns.Datetime()
        updated_at = columns.Datetime()

    def api_demo(widgets: Widget) -> Widget:
        thinga = widgets.create({"name": "Thinga", "category": "Doohickey", "cost": 125})
        mabob = widgets.create({"name": "Mabob", "category": "Doohicky", "cost": 150})
        return widgets

    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(
            api_demo,
            model_class=Widget,
            return_records=True,
            readable_column_names=["id", "name", "category", "cost", "created_at", "updated_at"],
        ),
        classes=[Widget]
    )
    cli()
    ```

    The above app declares a model class that matches the output from our server/api.  Note that the id,
    created_at, and updated_at columns all changed types to their "plain" types.  This is very normal.  The API
    is the one that is responsible for assigning ids and setting created/updated timestamps, so from the
    perspective of our client, these are plain string/datetime fields.  If we used the UUID or created/updated
    columns, then when the client called the API it would try to set all of these columns.  Since they are not
    writeable columns, the API would return an input error.  If you launch the above server/API and then run
    the given client script, you'll see output like this:

    ```
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "54eef01d-7c87-4959-b525-dcb9047d9692",
                "name": "Mabob",
                "category": "Doohicky",
                "cost": 150.0,
                "created_at": "2025-06-13T15:19:27+00:00",
                "updated_at": "2025-06-13T15:19:27+00:00"
            },
            {
                "id": "ed1421b8-88ad-49d2-a130-c34b4ac4dfcf",
                "name": "Thinga",
                "category": "Doohickey",
                "cost": 125.0,
                "created_at": "2025-06-13T15:19:27+00:00",
                "updated_at": "2025-06-13T15:19:27+00:00"
            }
        ],
        "pagination": {},
        "input_errors": {}
    }

    ```
    """
    is_public = False
    can_authorize = False

    environment = clearskies.di.inject.Environment()
    secrets = clearskies.di.inject.Secrets()

    """
    The path in our secret manager from which the secret should be fetched.

    Of course, to use `secret_key`, you must also provide a secret manager.  The below example uses the dependency
    injection system to create a faux secret manager to demonstrate how it works in general:

    ```
    from types import SimpleNamespace
    import clearskies

    def fetch_secret(path):
        if path == "/path/to/my/secret":
            return "SUPERSECRET"
        raise KeyError(f"Attempt to fetch non-existent secret: {path}")

    fake_secret_manager = SimpleNamespace(get=fetch_secret)

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Callable(
            lambda: {"hello": "world"},
            authentication=clearskies.authentication.SecretBearer(secret_key="/path/to/my/secret"),
        ),
        bindings={
            "secrets": fake_secret_manager,
        },
    )
    wsgi()
    ```

    And when invoked:

    ```
    $ curl 'http://localhost:8080/' -H "Authorization: SUPERSECRET" | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "hello": "world"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/' -H "Authorization: definitely-not-the-api-key" | jq
    {
        "status": "client_error",
        "error": "Not Authenticated",
        "data": [],
        "pagination": {},
        "input_errors": {}
    }
    ```

    """
    secret_key = clearskies.configs.String(default="")

    """
    The path in our secret manager where an alternate secret can also be fetched

    The alternate secret is exclusively used to authenticate incoming requests.  This allows for secret
    rotation - Point secret_key to a new secret and alternate_secret_key to the old secret.  Both will then
    be accepted and you can migrate your applications to only send the new secret.  Once they are all updated,
    remove the alternate_secret_key:

    ```
    from types import SimpleNamespace
    import clearskies

    def fetch_secret(path):
        if path == "/path/to/my/secret":
            return "SUPERSECRET"
        if path == "/path/to/alternate/secret":
            return "ALSOOKAY"
        raise KeyError(f"Attempt to fetch non-existent secret: {path}")

    fake_secret_manager = SimpleNamespace(get=fetch_secret)

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Callable(
            lambda: {"hello": "world"},
            authentication=clearskies.authentication.SecretBearer(
                secret_key="/path/to/my/secret",
                alternate_secret_key="/path/to/alternate/secret",
            ),
        ),
        bindings={
            "secrets": fake_secret_manager,
        },
    )
    wsgi()
    ```

    And when invoked:

    ```
    $ curl 'http://localhost:8080/' -H "Authorization: SUPERSECRET" | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "hello": "world"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/' -H "Authorization: ALSOOKAY" | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "hello": "world"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/' -H "Authorization: NOTTHESECRET" | jq
    {
        "status": "client_error",
        "error": "Not Authenticated",
        "data": [],
        "pagination": {},
        "input_errors": {}
    }
    ```

    """
    alternate_secret_key = clearskies.configs.String(default="")

    """
    The name of the environment variable from which we should fetch our key.
    """
    environment_key = clearskies.configs.String(default="")

    """
    The name of an alternate environment variable from which we should fetch our key.

    This allows for secret rotation by allowing the API to accept a secret from two different
    environment variables: an old value and a new value.  You can then migrate your client applications
    to use the new key and, once they are all migrated, remove the old key from the application
    configuration.  Here's an example:

    ```
    import os
    import clearskies

    os.environ["MY_AUTH_SECRET"] = "SUPERSECRET"
    os.environ["MY_ALT_SECRET"] = "ALSOOKAY"

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Callable(
            lambda: {"hello": "world"},
            authentication=clearskies.authentication.SecretBearer(
                environment_key="MY_AUTH_SECRET",
                alternate_environment_key="MY_ALT_SECRET",
            ),
        ),
    )
    wsgi()
    ```

    And when invoked:

    ```
    $ curl 'http://localhost:8080/' -H "Authorization: SUPERSECRET" | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "hello": "world"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/' -H "Authorization: ALSOOKAY" | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "hello": "world"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/' -H "Authorization: NOTTHESECRET" | jq
    {
        "status": "client_error",
        "error": "Not Authenticated",
        "data": [],
        "pagination": {},
        "input_errors": {}
    }
    ```

    """
    alternate_environment_key = clearskies.configs.String(default="")

    """
    The expected prefix (if any) that should come before the secret key in the authorization header.

    This applies to both the incoming authentication process and outgoing authentication headers.  Some systems
    require a prefix before the auth token in the HTTP header (e.g. `Authorization: TOKEN [auth key here]`).
    You can provide that prefix to `header_prefix` in order for the endpoint to require a prefix or the api backend
    to provide such a prefix.  Note that the prefix is case-insensitive and it does not assume a space between the
    prefix and the token (so, if you want a space, you must explicitly put it in the prefix).  Here's an example:

    ```
    import os
    import clearskies

    os.environ["MY_AUTH_SECRET"] = "SUPERSECRET"

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Callable(
            lambda: {"hello": "world"},
            authentication=clearskies.authentication.SecretBearer(
                environment_key="MY_AUTH_SECRET",
                header_prefix="secret-token ",
            ),
        ),
    )
    wsgi()
    ```

    And then usage:

    ```
    $ curl 'http://localhost:8080/' -H "Authorization: SECRET-TOKEN SUPERSECRET" | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "hello": "world"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/' -H "Authorization: SUPERSECRET" | jq
    {
        "status": "client_error",
        "error": "Not Authenticated",
        "data": [],
        "pagination": {},
        "input_errors": {}
    }
    ```
    """
    header_prefix = clearskies.configs.String(default="")

    """
    The length of our header prefix
    """
    header_prefix_length = None

    """
    The name of our security scheme in the auto-generated documentation
    """
    documentation_security_name = clearskies.configs.String(default="ApiKey")

    _secret: str = None #  type: ignore
    _alternate_secret: str = None # type: ignore

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        secret_key: str="",
        alternate_secret_key: str="",
        environment_key: str="",
        alternate_environment_key: str="",
        header_prefix: str="",
        documentation_security_name: str="",
    ):
        if not secret_key and not environment_key:
            raise ValueError(
                "Must set either 'secret_key' or 'environment_key' when configuring the SecretBearer"
            )
        self.header_prefix_length = len(header_prefix)
        self.finalize_and_validate_configuration()

    @property
    def secret(self):
        if not self._secret:
            self._secret = self.secrets.get(self.secret_key) if self.secret_key else self.environment.get(self.environment_key)
        return self._secret

    def clear_credential_cache(self):
        if self.secret_key:
            self._secret = None

    @property
    def alternate_secret(self):
        if not self.alternate_secret_key and not self.alternate_environment_key:
            return ""

        if not self._alternate_secret:
            self._alternate_secret = self.secrets.get(self.alternate_secret_key) if self.secret_key else self.environment.get(self.alternate_environment_key)
        return self._alternate_secret

    def headers(self, retry_auth=False):
        self._configured_guard()
        if retry_auth:
            self.clear_credential_cache()
        return {"Authorization": f"{self.header_prefix}{self.secret}"}

    def authenticate(self, input_output):
        self._configured_guard()
        auth_header = input_output.request_headers.authorization
        if not auth_header:
            return False
        if auth_header[: self.header_prefix_length].lower() != self.header_prefix.lower():
            # self._logging.debug(
            #     "Authentication failure due to prefix mismatch.  Configured prefix: "
            #     + self._header_prefix.lower()
            #     + ".  Found prefix: "
            #     + auth_header[: self._header_prefix_length].lower()
            # )
            return False
        provided_secret = auth_header[self.header_prefix_length :]
        if self.secret == provided_secret:
            # self._logging.debug("Authentication success")
            return True
        if self.alternate_secret and provided_secret == self._alternate_secret:
            # self._logging.debug("Authentication success with alternate secret")
            return True
        # self._logging.debug("Authentication failure due to secret mismatch")
        return False

    def authorize(self, authorization):
        raise ValueError("SecretBearer does not support authorization")

    def set_headers_for_cors(self, cors):
        cors.add_header("Authorization")

    def _configured_guard(self):
        if not self.secret:
            raise ValueError("Attempted to use SecretBearer authentication class without providing the configuration")

    def documentation_request_parameters(self):
        return []

    def documentation_security_scheme(self):
        return {
            "type": "apiKey",
            "name": "authorization",
            "in": "header",
        }

    def documentation_security_scheme_name(self):
        return self.documentation_security_name
