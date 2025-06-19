from __future__ import annotations

import inspect
from typing import Any, Callable, Type

import clearskies.configs
import clearskies.exceptions
from clearskies import autodoc, typing
from clearskies.endpoint import Endpoint
from clearskies.functional import routing, string
from clearskies.input_outputs import InputOutput


class HealthCheck(Endpoint):
    """
    An endpoint that returns 200/500 to denote if backend services are functional.

    You can provide dependency injection names, classes, or a callable.  When invoked, this endpoint
    will build/call all of them and, as long as none raise any exceptions, return a 200.

    HealthCheck endpoints are always public and ignore authentication/authorization settings.

    If you don't provide any configuration to the endpoint, it will always succeed:

    ```python
    import clearskies

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.HealthCheck(),
    )
    wsgi()
    ```

    which when invoked:

    ```bash
    $ curl 'http://localhost:8080' | jq
    {
        "status": "success",
        "error": "",
        "data": {},
        "pagination": {},
        "input_errors": {}
    }
    ```

    This example demonstrates a failed healthcheck by requesting the cursor (which attempts to connect to the database).
    Since no database has been setup/configured, it always fails:

    ```python
    import clearskies

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.HealthCheck(
            dependency_injection_names=["cursor"],
        ),
    )
    wsgi()
    ```

    And when invoked returns:

    ```bash
    $ curl 'http://localhost:8080' | jq
    {
        "status": "failure",
        "error": "",
        "data": {},
        "pagination": {},
        "input_errors": {}
    }
    ```

    with a status code of 500.
    """

    """
    A list of dependency injection names that should be fetched when the healthcheck endpoint is invoked.

    If any exceptions are raised when building the dependency injection parameters, the health check will return
    failure.
    """
    dependency_injection_names = clearskies.configs.StringList(default=[])

    """
    A list of classes to build with the dependency injection system.

    The If any exceptions are raised when building the classes, then the healthcheck will return a failure.
    In the following example, since the class-to-build requests the cursor, and we don't have a reachable
    database configured,

    ```python
    import clearskies

    class MyClass:
        def __init__(self, cursor):
            pass

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.HealthCheck(
            classes_to_build=[MyClass],
        ),
    )
    wsgi()
    ```
    """
    classes_to_build = clearskies.configs.Any(default=[])

    """
    A list of callables to invoke.

    Your callables can request any dependency injection names.  If any exceptions are raised, the healthcheck will
    return a failure.  The return value from the function is ignored.  In this example we request the cursor from
    the dependency injection system, which will call the healthcheck to fail since we don't have a database setup
    and configured:

    ```python
    import clearskies

    def my_function(cursor):
        pass

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.HealthCheck(
            callables=[my_function],
        ),
    )
    wsgi()
    ```
    """
    callables = clearskies.configs.Any(default=[])

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        dependency_injection_names: list[str] = [],
        classes_to_build: list[type] = [],
        callables: list[Callable] = [],
        description: str = "",
        url: str = "",
        request_methods: list[str] = ["GET"],
    ):
        # we need to call the parent but don't have to pass along any of our kwargs.  They are all optional in our parent, and our parent class
        # just stores them in parameters, which we have already done.  However, the parent does do some extra initialization stuff that we need,
        # which is why we have to call the parent.
        super().__init__()

    def handle(self, input_output: InputOutput) -> Any:
        try:
            for name in self.dependency_injection_names:
                self.di.build_from_name(name)

            for class_to_build in self.classes_to_build:
                self.di.build_class(class_to_build)

            for thing_to_call in self.callables:
                self.di.call_function(thing_to_call)
        except:
            return self.failure(input_output)

        return self.success(input_output, {})

    def documentation(self) -> list[autodoc.request.Request]:
        output_schema = self.model_class
        nice_model = string.camel_case_to_words(output_schema.__name__)
        output_autodoc = (autodoc.schema.Object(self.auto_case_internal_column_name("data"), children=[]),)

        description = self.description if self.description else "Health Check"
        return [
            autodoc.request.Request(
                description,
                [
                    self.documentation_success_response(
                        output_autodoc,  # type: ignore
                        description=description,
                    ),
                ],
                relative_path=self.url,
                request_methods=self.request_methods,
            ),
        ]
