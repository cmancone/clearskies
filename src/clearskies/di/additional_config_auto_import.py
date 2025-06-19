from .additional_config import AdditionalConfig


class AdditionalConfigAutoImport(AdditionalConfig):
    """
    AdditionalConfig, but now with auto import.

    This works exactly like the AdditionalConfig class, but will be automatically imported into the Di
    container if found in a module being imported into the Di container.  This just provides a way for
    modules to easily inject names into the Di system.  In order to be found, an imported module
    just needs to make sure that it imports the class that extends the AdditionalConfigAutoImport class.

    Note that automatically-imported AdditionalConfig classes automatically have lower priority than
    any AdditionalConfig classes added explicitly to the Di container.
    """

    pass
