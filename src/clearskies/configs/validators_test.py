import unittest
from unittest.mock import MagicMock

from clearskies import configs, parameters_to_properties
from .. import validator
from clearskies.bindings import Validator as BindingValidator

class FakeValidator(validator.Validator):
    def check(self, data):
        pass

class HasConfigs(configs.Configurable):
    validators = configs.Validators()

    @parameters_to_properties
    def __init__(self, validators):
        self.finalize_and_validate_configuration()

class ValidatorsTest(unittest.TestCase):
    def test_allow(self):
        binding_validator = BindingValidator(ValidatorsTest)
        fake_validator = FakeValidator()

        has_configs = HasConfigs(fake_validator)
        assert has_configs.validators == [fake_validator]

        more_configs = HasConfigs([binding_validator, fake_validator])
        assert more_configs.validators == [binding_validator, fake_validator]

    def test_raise_non_action(self):
        with self.assertRaises(TypeError) as context:
            fake_validator = FakeValidator()
            has_configs = HasConfigs([fake_validator, "sup"])
        assert "Error with 'HasConfigs.validators': attempt to set a value of type 'str' for item #2 when a Validator or BindingValidator is required" == str(context.exception)
