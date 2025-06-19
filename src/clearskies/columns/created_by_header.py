import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.columns.string import String
from clearskies.query import Condition


class CreatedByHeader(String):
    """
    This column will automatically take data from the header attached to a request and store it in the model upon creation.

    If header data isn't available from the context being executed, then you may end up with an error
    (depending on the context).  This is a good thing if you are trying to consistely provide audit information,
    but may be a problem if your model creation needs to happen more flexibly.

    NOTE: columns generally also have the `created_by_source_type` and `created_by_source_key` properties that perform
    this exact same function.  Why do we have those properties and this column?  This column works well if we have
    some simple string values that we want to always pull from the header data.  The properties work better if you need to
    pull header data but it's not just a string type.  An example might be if you wanted to pull the user id out of the
    header data to populate a `BelongsToId` column.  You wouldn't use this column because it can't provide all the functionality
    related to `BelongsToId`, so instead you would use the `BelongsToId` column and set `created_by_source_type` to `http_header` and
    `created_by_source_key` to `user_id`.  Example usage:

    ```python
    import clearskies


    class MyModel(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        custom_header = clearskies.columns.CreatedByHeader("my_custom_header")


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            MyModel,
            writeable_column_names=["name"],
            readable_column_names=["id", "name", "custom_header"],
        ),
        classes=[MyModel],
    )
    wsgi()
    ```

    If you invoked this:

    ```bash
    $ curl 'http://localhost:8080' -d '{"name":"Bob"}' -H 'my_custom_header: some header value' | jq

    {
        "status": "success",
        "error": "",
        "data": {
            "id": "10459ee4-a75e-4fd1-9993-2feeea629144",
            "name": "Bob",
            "custom_header": "some header value"
        },
        "pagination": {},
        "input_errors": {}
    }

    ```
    """

    """
    The name of the header that this column should be populated from.
    """
    header_name = configs.String(required=True)

    """
    Whether or not to throw an error if the key is not present in the header data.
    """
    strict = configs.Boolean(default=True)

    """
    Since this column is always populated automatically, it is never directly writeable.
    """
    is_writeable = configs.Boolean(default=False)
    _descriptor_config_map = None

    _allowed_search_operators = ["=", "in", "is not null", "is null", "like"]

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        header_name: str,
        strict: bool = True,
        is_readable: bool = True,
        is_searchable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
    ):
        self.created_by_source_key = header_name
        self.created_by_source_type = "http_header"
