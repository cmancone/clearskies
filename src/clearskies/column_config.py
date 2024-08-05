from typing import Any, Callable, List, Optional, Union

from clearskies.bindings import Action as BindingAction
from . import configs
from .action import Action
from .validator import Validator
from clearskies.bindings import Validator as BindingValidator


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
    validators = configs.Validators(default=[])
    is_writeable = configs.Boolean(default=False)
    is_temporary = configs.Boolean(default=False)
    on_change_pre_save = configs.Actions(default=[])
    on_change_post_save = configs.Actions(default=[])
    on_change_save_finished = configs.Actions(default=[])
    default = configs.String(default=None)
    setable = configs.String(default=None)
    created_by_source_key = configs.String(default="")
    created_by_source_type = configs.Select(["authorization_data"])

    def __init__(
        self,
        validators: Union[Callable, Validator, BindingValidator, List[Union[Callable, Action, BindingAction]]] = [],
        is_writeable: bool = False,
        is_temporary: bool = False,
        on_change_pre_save: Union[Callable, Action, BindingAction, List[Union[Callable, Action, BindingAction]]] = [],
        on_change_post_save: Union[Callable, Action, BindingAction, List[Union[Callable, Action, BindingAction]]] = [],
        on_change_save_finished: Union[
            Callable, Action, BindingAction, List[Union[Callable, Action, BindingAction]]
        ] = [],
        default: Optional[str] = None,
        setable: Optional[str] = None,
        created_by_source_type: str = "",
        created_by_source_key: str = "",
    ):
        self.validators = validators
        self.is_writeable = is_writeable
        self.is_temporary = is_temporary
        self.finalize_and_validate_configuration()

    def __get__(self, instance, parent) -> str:
        if not instance:
            return self  # type: ignore

        return instance._data[self._my_name(instance)]

    def __set__(self, instance, value: str) -> None:
        instance._next_data[self._my_name(instance)] = value

    def _my_name(self, instance) -> str:
        """
        Returns the name of this column

        We don't know what our name is because it's determined by the attribute we are assigned
        to in the model, and we don't have the context to know what that is.  We could have the model
        tell us our name, but it's slightly lazier to simply ask the model when it actually matters.
        It only matters during __get__ and __set__, and in both of those cases we are passed the model.
        Therefore, we'll ask the model what our name is.
        """
        if not self.name:
            self.name = instance.lookup_column_name(self)

        return self.name

    def finalize_and_validate_configuration(self):
        super().finalize_and_validate_configuration()

        if self.setable is not None and self.created_by_source_type:
            raise ValueError("You attempted to set both 'setable' and 'created_by_source_type', but these configurations are mutually exclusive.  You can only set one for a given column")

        if (self.created_by_source_type and not self.created_by_source_key) or (not self.created_by_source_type and self.created_by_source_key):
            raise ValueError("You only set one of 'created_by_source_type' and 'created_by_source_key'.  You have to either set both of them (which enables the 'created_by' feature of the column) or you must set neither of them.")
