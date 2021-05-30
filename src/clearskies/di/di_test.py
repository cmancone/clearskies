import unittest
from unittest.mock import MagicMock, call
from .di import DI
from .. import BindingConfig

class MoreStuff:
    def __init__(self, some_class):
        self.some_class = some_class

    def configure(self, age=None):
        self.age=age

class SomeClass:
    pass

class more_classes:
    def __init__(self, arbitrarily_defined):
        self.arbitrarily_defined = arbitrarily_defined

class AnotherClass:
    def __init__(self, some_class, more_classes):
        self.some_class = some_class
        self.more_classes = more_classes

class ModelTest(unittest.TestCase):
    def setUp(self):
        self.di = DI(classes=[SomeClass, more_classes, AnotherClass])
        self.di.bind('arbitrarily_defined', BindingConfig(MoreStuff, age=2))

    def test_simple_build_from_string(self):
        value = self.di.build('arbitrarily_defined')
        self.assertEquals(MoreStuff.__name__, value.__class__.__name__)
        self.assertEquals(2, value.age)
