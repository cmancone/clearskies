import clearskies.typing
from clearskies.columns.column import Column
from clearskies import configs, parameters_to_properties


class CreatedByHeader(Column):
    """
    This column will automatically take data from the header attached to a request and store it in the model upon creation.

    If header data isn't available from the context being executed, then you may end up with an error
    (depending on the context).  This is a good thing if you are trying to consistely provide audit information,
    but may be a problem if your model creation needs to happen more flexibly.

    NOTE: columns generally also have the `created_by_source_type` and `created_by_source_key` properties that perform
    this exact same function.  Why do we have those properties and this column?  This column works well if we have
    some simple string values that we want to always pull from the header data.  The properties work better if you need to
    pull header data but it's not just a string type.  An example might be if you wanted to pull the user id out of the
    header data to populate a `BelongsTo` column.  You wouldn't use this column because it can't provide all the functionality
    related to `BelongsTo`, so instead you would use the `BelongsTo` column and set `created_by_source_type` to `http_header` and
    `created_by_source_key` to `user_id`.
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

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        header_name: str,
        strict: bool = True,
        is_readable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
    ):
        pass
