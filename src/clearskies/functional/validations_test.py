import unittest
from . import validations
from ..model import Model
class User(Model):
    def __init__(self):
        super().__init__('backend', 'columns')

    def columns_configuration(self):
        return []
class ValidationsTest(unittest.TestCase):
    def test_is_model(self):
        self.assertTrue(validations.is_model(User()))
        self.assertFalse(validations.is_model(''))

    def test_is_model_class(self):
        self.assertTrue(validations.is_model_class(User))
        self.assertFalse(validations.is_model_class(''))
        self.assertFalse(validations.is_model_class(User()))

    def test_is_model_or_class(self):
        self.assertTrue(validations.is_model_or_class(User))
        self.assertTrue(validations.is_model_or_class(User()))
        self.assertFalse(validations.is_model_or_class(''))
