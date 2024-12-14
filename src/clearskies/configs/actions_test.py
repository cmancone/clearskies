import unittest
from unittest.mock import MagicMock
from clearskies import configs, Configurable, parameters_to_properties
from .. import action


class FakeAction(action.Action):
    def __call__(self):
        pass


class HasConfigs(Configurable):
    actions = configs.Actions()

    @parameters_to_properties
    def __init__(self, actions):
        self.finalize_and_validate_configuration()


class ActionsTest(unittest.TestCase):
    def test_allow(self):
        has_configs = HasConfigs(self.test_allow)
        assert has_configs.actions == [self.test_allow]

        fake_action = FakeAction()
        more_configs = HasConfigs([self.test_allow, fake_action])
        assert more_configs.actions == [self.test_allow, fake_action]

    def test_raise_non_action(self):
        with self.assertRaises(TypeError) as context:
            fake_action = FakeAction()
            has_configs = HasConfigs([self.test_allow, fake_action, "sup"])
        assert (
            "Error with 'HasConfigs.actions': attempt to set a value of type 'str' for item #3 when a callable or Action is required"
            == str(context.exception)
        )
