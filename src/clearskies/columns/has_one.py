from clearskies.columns.has_many import HasMany


class HasOne(HasMany):
    """
    This operates exactly like the HasMany relationship, except it assumes there is only ever one child.

    The only real difference between this and HasMany is that the HasMany column type will return a list
    of models, while this returns the first model.
    """

    _descriptor_config_map = None

    pass
