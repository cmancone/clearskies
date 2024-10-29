from typing import List

from clearskies.configs import config


class ModelColumns(config.Config):
    def __init__(self, model_class_parameter: str, required=False, default=None):
        """
        ModelColumns is a configuration that provides a list of
        """
        super().__init__(required=required, default=default)
        self.model_class_parameter = model_class_parameter

    def __set__(self, instance, value: List[str]):
        if not isinstance(value, list):
            error_prefix = self._error_prefix(instance)
            raise TypeError(f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' but a ModelClass config must be set to a list containing the names of columns")

        for (item, index) in enumerate(value):
            if isinstance(item, str):
                continue

            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{item.__class__.__name__}' for item #{index+1} when a string is required"
            )

        instance._set_config(self, value)

    def __get__(self, instance, parent) -> List[Union[str]]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)

    def finalize_and_validate_configuration(self, instance):
        super().finalize_and_validate_configuration(instance)
        instance_class = instance.__class__

        # the model class
        if not hasattr(instance, self.model_class_parameter):
            error_prefix = self._error_prefix(instance)
            raise ValueError(
                f"{error_prefix} 'model_class_parameter' is set to `{instance_class.__name__}.{self.model_class_parameter}`, but this configuration does not actually exist in '{instance_class.__name__}'"
            )

        model_class_config = getattr(instance_class, self.model_class_parameter)
        #if not isinstance(model_class_config, model_class.ModelClass):
            #error_prefix = self._error_prefix(instance)
            #raise TypeError(
                #f"{error_prefix} 'model_class_parameter' is set to `{instance_class.__name__}.{self.model_class_parameter}`, which should be a configuration of type 'clearskies.configs.ModelClass', but instead it has the type of {model_class_config.__class__.__name__}"
            #)

        model_column_configs = getattr(instance, self.model_class_parameter).column_configs()
        for (index, column_name) in self.__get__(instance, instance_class):
            self._column_name_checks(index, column_name, instance, model_column_configs)

    def _column_name_checks(self, index, column_name, instance, model_column_configs):
        if column_name not in model_column_configs:
            error_prefix = self._error_prefix(instance)
            raise ValueError(
                f"{error_prefix} item #{index+1} specifies a column named '{column_name}' but this column does not exist in the model class, '{instance.__class__.__name__}'.  The available columns are: '" + "', '".join(model_column_configs.keys()) + "'"
            )
