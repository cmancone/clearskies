from typing import Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties


class ColumnConfig(configs.Configurable):
    """
    The base column config.

    This class (well, the children that extend it) are used to define the columns
    that exist in a given model class.  See the note on the columns module itself for full
    details of what that looks like.

    These objects themselves don't ever store data that is specifc to a model because
    of their lifecycle - they are bound to the model *class*, not to an individual model
    instance.  Thus, any information stored in the column config will be shared by
    all instances of that model.
    """

    """
    A default value to set for this column.

    The default is only used when creating a record for the first time, and only if
    a value for this column has not been set.
    """
    default = configs.String(default=None)

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.StringOrCallable(default=None)

    """
    Whether or not this column can be converted to JSON and included in an API response.
    """
    is_readable = configs.Boolean(default=True)

    """
    Whether or not this column can be set via an API call.
    """
    is_writeable = configs.Boolean(default=True)

    """
    Whether or not this column is temporary.  A temporary column is not persisted to the backend.
    """
    is_temporary = configs.Boolean(default=False)

    """
    Validators to use when checking the input for this column during write operations from the API.

    Keep in mind that the validators are only checked when the column is exposed via a supporting handler.
    You can still set whatever values you want when saving the model directly, e.g. `model.save(...)`
    """
    validators = configs.Validators(default=[])

    """
    Actions to take during the pre-save step of the save process if the column has changed in the save.

    Pre-save happens before the data is persisted to the backend.  Actions/callables in
    this step can return a dictionary of additional data to include in the save operation.

    Since the save hasn't completed, any data in the model itself reflects the model before the save
    operation started.

    Callables and actions can request any dependencies provided by the DI system.  In addition, they can request
    two named parameters:

     1. `model` - the model involved in the save operation
     2. `data` - the new data being saved

    The `is_changing` and `latest` methods on the model class are useful here, so give them a read.
    """
    on_change_pre_save = configs.Actions(default=[])

    """
    Actions to take during the post-save step of the process if the column has changed in the save.

    Post-save happens after the data is persisted to the backend but before the full save process has finished.
    Since the data has been persisted to the backend,any data returned by the callables/actions will be ignored.
    If you need to make data changes you'll have to execute a separate save operation.

    Since the save hasn't finished, the model is not yet updated with the new data, and
    any data you fetch out of the model will refelect the data in the model before the save started.

    Callables and actions can request any dependencies provided by the DI system.  In addition, they can request
    two named parameters:

     1. `model` - the model involved in the save operation
     2. `data` - the new data being saved

    The `is_changing` and `latest` methods on the model class are useful here, so give them a read.
    """
    on_change_post_save = configs.Actions(default=[])

    """
    Actions to take during the save-finished step of the save process if the column has changed in the save.

    Save-finished happens after the save process has completely finished and the model is updated with
    the final data.  Any data returned by these actions will be ignored, since the save has already finished.
    If you need to make data changes you'll have to execute a separate save operation.

    Callables and actions can request any dependencies provided by the DI system.  In addition, they can request
    the following parameter:

     1. `model` - the model involved in the save operation

    Unlike pre_save and post_save, `data` is not provided because this data has already been merged into the
    model.  To understand more about the save operation, use methods like `was_changed` and `previous_value`.

    """
    on_change_save_finished = configs.Actions(default=[])

    """
    Use in conjunction with `created_by_source_type` to have this column automatically populated by data from an HTTP request.

    So, for instance, setting `created_by_source_type` to `authorization_data` and setting this to `email`
    will result in the email value from the authorization data being persisted into this column when the
    record is saved.

    NOTE: this is sometimes best set as a column override on an API handler definition, rather than directly
    on the model itself.  The reason is because the authorization data and header information is typically
    only available during an HTTP request, so if you set this on the model level, you'll get an error
    if you try to make saves to the model in a context where authorization data and/or headers don't exist.
    """
    created_by_source_key = configs.String(default="")

    """
    Use in conjunction with `created_by_source_key` to have this column automatically populated by data from ann HTTP request.

    So, for instance, setting this to `authorization_data` and setting `created_by_source_key` to `email`
    will result in the email value from the authorization data being persisted into this column when the
    record is saved.

    NOTE: this is sometimes best set as a column override on an API handler definition, rather than directly
    on the model itself.  The reason is because the authorization data and header information is typically
    only available during an HTTP request, so if you set this on the model level, you'll get an error
    if you try to make saves to the model in a context where authorization data and/or headers don't exist.
    """
    created_by_source_type = configs.Select(["authorization_data", "http_header", "routing_data"])

    """ The model class this column is associated with. """
    model_class = configs.ModelClass()

    """ The name of this column. """
    name = configs.String()

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: str | None = None,
        setable: str | Callable[..., str] | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_temporary: bool = False,
        validators: clearskies.typing.validators | list[clearskies.typing.validators] = [],
        on_change_pre_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_post_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_save_finished: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
    ):
        pass

    def finalize_configuration(self, model_class, name) -> None:
        """
        Finalize and check the configuration.

        This is an external trigger called by the model class when the model class is ready.
        The reason it exists here instead of in the constructor is because some columns are tightly
        connected to the model class, and can't validate configuration until they know what the model is.
        Therefore, we need the model involved, and the only way for a property to know what class it is
        in is if the parent class checks in (which is what happens here).
        """
        self.model_class = model_class
        self.name = name
        self.finalize_and_validate_configuration()

    def __get__(self, instance, parent) -> str:
        if not instance:
            return self  # type: ignore

        return instance._data[self.name]

    def __set__(self, instance, value: str) -> None:
        instance._next_data[self.name] = value

    def finalize_and_validate_configuration(self):
        super().finalize_and_validate_configuration()

        if self.setable is not None and self.created_by_source_type:
            raise ValueError("You attempted to set both 'setable' and 'created_by_source_type', but these configurations are mutually exclusive.  You can only set one for a given column")

        if (self.created_by_source_type and not self.created_by_source_key) or (not self.created_by_source_type and self.created_by_source_key):
            raise ValueError("You only set one of 'created_by_source_type' and 'created_by_source_key'.  You have to either set both of them (which enables the 'created_by' feature of the column) or you must set neither of them.")
