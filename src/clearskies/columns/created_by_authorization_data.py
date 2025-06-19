from __future__ import annotations

from typing import TYPE_CHECKING, Any

import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.columns.string import String

if TYPE_CHECKING:
    from clearskies import Model


class CreatedByAuthorizationData(String):
    """
    This column will automatically take data from the authorization data attached to a request and store it in the model upon creation.

    If authorization data isn't available from the context being executed, then you may end up with an error
    (depending on the context).  This is a good thing if you are trying to consistely provide audit information,
    but may be a problem if your model creation needs to happen more flexibly.  Obviously, a pre-requisite for using this
    class is to have an authentication class attached to your endpoint which populates the authorization data.

    NOTE: columns generally also have the `created_by_source_type` and `created_by_source_key` properties that perform
    this exact same function.  Why do we have those properties and this column?  This column works well if we have
    some simple string values that we want to always pull from the authorization data (email, for instance).  The
    properties work better if you need to pull authorization data but it's not just a string type.  An example might
    be if you wanted to pull the user id out of the authorziation data to populate a `BelongsToId` column.  You wouldn't
    use this column because it can't provide all the functionality related to `BelongsToId`, so instead you would
    use the `BelongsToId` column and set `created_by_source_type` to `authorization_data` and `created_by_source_key` to `user_id`.
    Example usage:

    ```python
    class MyModel(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        organization_id = clearskies.columns.CreatedByAuthorizationData("organization_id")


    class MyAuthentication(clearskies.authentication.Authentication):
        def authenticate(self, input_output) -> bool:
            # Authenticate the user!
            #
            # This is where you would normally authenticate the user and provide any data about them to the
            # authorization system.  This might mean validating a JWT and then providing the claims as authorization data,
            # or looking up a session id and providing the session data to the authorization system.  In this case,
            # we're just going to return a fixed id for our organization.
            input_output.authorization_data = {
                "organization_id": "my-super-awesome-organization",
            }
            return True


    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Create(
            MyModel,
            writeable_column_names=["name"],
            readable_column_names=["id", "name", "organization_id"],
            authentication=MyAuthentication(),
        ),
        classes=[MyModel],
    )
    cli()
    ```

    And running this will give you something like:

    ```json
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "49816ea4-0956-461e-abd4-03dbde845ba9",
            "name": "Bob",
            "organization_id": "my-super-awesome-organization",
        },
        "pagination": {},
        "input_errors": {},
    }
    ```
    """

    """
    The key inside the authorization data that should be pulled into the column value when the record is created
    """
    authorization_data_key_name = configs.String(required=True)

    """
    Whether or not to throw an error if the key is not present in the authorization data.
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
        authorization_data_key_name: str,
        strict: bool = True,
        is_readable: bool = True,
        is_searchable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
    ):
        self.created_by_source_key = authorization_data_key_name
        self.created_by_source_type = "authorization_data"
