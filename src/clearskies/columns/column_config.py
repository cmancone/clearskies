from typing import Any, Callable, List, Union

from clearskies import configs
from clearskies.bindings import Action as BindingAction
from clearskies.actions import Action
from clearskies.bindings import Validator as BindingValidator
from clearskies.columns.validators import Validator


class ColumnConfig(configs.Configurable):
    validators = configs.Validators()
    is_writeable = configs.Boolean(default=False)
    is_temporary = configs.Boolean(default=False)
    on_change_pre_save = configs.Actions()
    on_change_post_save = configs.Actions()
    on_change_save_finished = configs.Actions()
    default = configs.Any()
    created_by_source_key = configs.String()
    created_by_source_type = configs.Select(["authorization_data"])

    @configs.parameters_to_properties
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
        default: Any = None,
        created_by_source_type: str = '',
        created_by_source_key: str = '',
    ):
        self.finalize_and_validate_configuration()

    def __get__(self, instance, parent) -> str:
        if not instance:
            return self  # type: ignore

        name = self._my_name(instance)

        # I didn't do it here, so self.name is hardcoded, but there
        # are some minor shenanigans I have to run through to tell the column
        # what it's name is.
        return parent._data[self.name]

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
