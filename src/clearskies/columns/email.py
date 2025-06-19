import re

from clearskies.columns.string import String


class Email(String):
    """
    A string column that specifically expects an email.

    ```python
    import clearskies


    class MyModel(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"

        id = clearskies.columns.Uuid()
        email = clearskies.columns.Email()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            MyModel,
            writeable_column_names=["email"],
            readable_column_names=["id", "email"],
        ),
        classes=[MyModel],
    )
    wsgi()
    ```

    And when invoked:

    ```bash
    $ curl 'http://localhost:8080' -d '{"email":"test@example.com"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "2a72a895-c469-45b0-b5cd-5a3cbb3a6e99",
            "email": "test@example.com"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080' -d '{"email":"asdf"}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "email": "Invalid email address"
        }
    }
    ```
    """

    _descriptor_config_map = None

    """
    A column that always requires an email address.
    """

    def input_error_for_value(self, value: str, operator: str | None = None) -> str:
        if type(value) != str:
            return f"Value must be a string for {self.name}"
        if operator and operator.lower() == "like":
            # don't check for an email if doing a fuzzy search, since we may be searching
            # for a partial email
            return ""
        if re.search(r"^[^@\s]+@[^@]+\.[^@]+$", value):
            return ""
        return "Invalid email address"
