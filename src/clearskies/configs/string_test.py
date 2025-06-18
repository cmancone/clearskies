import unittest
from unittest.mock import MagicMock

from clearskies import Configurable, configs, parameters_to_properties


class HasConfigs(Configurable):
    my_string = configs.String(default="asdf")

    @parameters_to_properties
    def __init__(self, my_string=None):
        self.finalize_and_validate_configuration()


class HasConfigsRequired(Configurable):
    my_string = configs.String(required=True)

    @parameters_to_properties
    def __init__(self, my_string=None):
        self.finalize_and_validate_configuration()


class StringTest(unittest.TestCase):
    def test_allow(self):
        has_configs = HasConfigs("something")
        assert has_configs.my_string == "something"

    def test_raise_wrong_type(self):
        with self.assertRaises(TypeError) as context:
            has_configs = HasConfigs(5)
        assert "Error with 'HasConfigs.my_string': attempt to set a value of type 'int' to a parameter that requires a string." == str(
            context.exception
        )

    def test_default(self):
        has_configs = HasConfigs()
        assert has_configs.my_string == "asdf"

    def test_required(self):
        with self.assertRaises(ValueError) as context:
            has_configs = HasConfigsRequired()
        assert "Missing required configuration property 'my_string' for class 'HasConfigsRequired'" == str(
            context.exception
        )
