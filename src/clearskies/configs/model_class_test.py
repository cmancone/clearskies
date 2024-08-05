import unittest
from unittest.mock import MagicMock
from clearskies import configs, Model, parameters_to_properties

class HasConfigs(configs.Configurable):
    some_model_class = configs.ModelClass()

    @parameters_to_properties
    def __init__(self, some_model_class):
        self.finalize_and_validate_configuration()

class ModelClassTest(unittest.TestCase):
    def test_allow_model(self):
        has_configs = HasConfigs(Model)
        assert has_configs.some_model_class == Model

    def test_raise_non_model(self):
        with self.assertRaises(TypeError) as context:
            has_configs = HasConfigs("hey")
        assert "Error with 'HasConfigs.some_model_class': attempt to set a value of type 'str' when a model class was expected" == str(context.exception)
