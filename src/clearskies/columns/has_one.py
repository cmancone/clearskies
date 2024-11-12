from clearskies.columns import has_many


class HasOne(has_many.HasMany):
    """
    This operates exactly like the HasMany relationship, except it assumes there is only ever one child.

    The only real difference between this and HasMany is that the HasMany column type will return a list
    of models, while this returns the first model.
    """
    pass
