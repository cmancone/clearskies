from .column import Column
from ..autodoc.schema import Boolean as AutoDocBoolean


class Boolean(Column):
    _auto_doc_class = AutoDocBoolean

    my_configs = {
        "on_true": None,
        "on_false": None,
    }

    def __init__(self, di):
        super().__init__(di)

    def _check_configuration(self, configuration):
        """Check the configuration and throw exceptions as needed"""
        super()._check_configuration(configuration)
        for trigger in ["on_true", "on_false"]:
            if configuration.get(trigger):
                self._check_actions(configuration[trigger], trigger)

    def to_backend(self, data):
        if self.name not in data or data[self.name] is None:
            return data

        return {
            **data,
            self.name: bool(data[self.name]),
        }

    def from_backend(self, value):
        return bool(value)

    def input_error_for_value(self, value, operator=None):
        return f"{self.name} must be a boolean" if type(value) != bool else ""

    def build_condition(self, value, operator=None, column_prefix=""):
        condition_value = "1" if value else "0"
        if not operator:
            operator = "="
        return f"{column_prefix}{self.name}{operator}{condition_value}"

    def save_finished(self, model):
        """
        Make any necessary changes needed after a save has completely finished.
        """
        super().save_finished(model)

        on_true = self.config("on_true", silent=True)
        on_false = self.config("on_false", silent=True)
        if not on_true and not on_false:
            return
        if not model.was_changed(self.name):
            return

        if model.get(self.name) and on_true:
            self.execute_actions(on_true, model)
        if not model.get(self.name) and on_false:
            self.execute_actions(on_false, model)
