from types import SimpleNamespace
import unittest
from . import validations
from clearskies import Model

class ValidationsTest(unittest.TestCase):
    def test_is_model(self):
        assert validations.is_model(SimpleNamespace(destination_name=True))
        assert not validations.is_model("")

    def test_is_model_class(self):
        assert validations.is_model_class(Model)
        assert not validations.is_model_class("")

    def test_is_model_or_class(self):
        assert validations.is_model_or_class(Model)
        assert validations.is_model_or_class(SimpleNamespace(destination_name=True))
        assert not validations.is_model_or_class("")
