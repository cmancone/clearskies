import clearskies.typing
from clearskies import parameters_to_properties
from clearskies.columns.has_many import HasMany


class HasManySelf(HasMany):
    """
    This is just like the HasMany column, but is used when the model references itself.

    This exists because a model can't refer to itself inside it's own class definition.  There are
    workarounds, but having this class is usually quicker for the developer.

    The main difference between this and HasMany is that you don't have to provide the child class.
    Also, the name of the column that contains the id of the parent becomes `parent_id` by default,
    rather than basing it on the name of the model.  This is done because, since the model is also
    the child, using the name of the model in the name of the column id is often ambiguous.

    See also BelongsToSelf.
    """

    _descriptor_config_map = None

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        foreign_column_name: str | None = None,
        readable_child_columns: list[str] = [],
        where: clearskies.typing.condition | list[clearskies.typing.condition] = [],
        is_readable: bool = True,
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
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
        self.child_model_class = model_class
        has_value = False
        try:
            has_value = bool(self.foreign_column_name)
        except KeyError:
            pass

        if not has_value:
            self.foreign_column_name = "parent_id"

        super().finalize_configuration(model_class, name)
