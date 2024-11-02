import unittest
from unittest.mock import MagicMock

from clearskies import configs
import clearskies.parameters_to_properties

class HasConfigs(configs.Configurable):
    my_select_list = configs.SelectList(["asdf", "qwerty", "bob", "jane"], default=["asdf", "bob"])

    @clearskies.parameters_to_properties
    def __init__(self, my_select_list=None):
        self.finalize_and_validate_configuration()

class SelectListTest(unittest.TestCase):
    def test_allow(self):
        has_configs = HasConfigs(["qwerty", "bob"])
        assert has_configs.my_select_list == ["qwerty", "bob"]

    def test_raise_wrong_type(self):
        with self.assertRaises(TypeError) as context:
            has_configs = HasConfigs(5)
        assert "Error with 'HasConfigs.my_select_list': attempt to set a value of type 'int' to a list parameter" == str(context.exception)

    def test_raise_invalid_value(self):
        with self.assertRaises(ValueError) as context:
            has_configs = HasConfigs(["asdf", "12345"])
        assert "Error with 'HasConfigs.my_select_list': attempt to set a value of '12345' for item #2.  This is not in the list of allowed values.  It must be one of 'asdf', 'qwerty', 'bob', 'jane'" == str(context.exception)

    def test_default(self):
        has_configs=HasConfigs()
        assert has_configs.my_select_list == ["asdf", "bob"]
