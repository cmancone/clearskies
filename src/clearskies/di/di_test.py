import unittest
from unittest.mock import MagicMock, call
from .di import DI
from .. import BindingConfig
from . import test_module, AdditionalConfig

class HasProvides(DI):
    def provide_blahblah(self, some_class):
        return [2, SomeClass]

class MoreStuff:
    def __init__(self, some_class, blahblah):
        self.some_class = some_class
        self.blahblah = blahblah

    def configure(self, age=None):
        self.age=age

class SomeClass:
    pass

class RequiresSubModule:
    def __init__(self, another_module_class):
        self.another_module_class = another_module_class

class Circular:
    def __init__(self, will_be_circular):
        pass

class WillBeCircular:
    def __init__(self, circular):
        pass

class more_classes:
    def __init__(self, arbitrarily_defined):
        self.arbitrarily_defined = arbitrarily_defined

class AnotherClass:
    def __init__(self, some_class, more_classes):
        self.some_class = some_class
        self.more_classes = more_classes

class MoreAdditionalConfig(AdditionalConfig):
    def provide_really_awesome_stuff(self, some_class):
        return MoreStuff(some_class, 'hey')

class ModelTest(unittest.TestCase):
    def setUp(self):
        self.di = HasProvides(classes=[SomeClass, more_classes, AnotherClass])
        self.di.bind('arbitrarily_defined', BindingConfig(MoreStuff, age=2))

    def test_simple_build_from_string(self):
        value = self.di.build('arbitrarily_defined')
        self.assertEquals(MoreStuff, value.__class__)
        self.assertEquals(2, value.age)
        self.assertEquals(SomeClass, value.some_class.__class__)

    def test_build_everything(self):
        value = self.di.build(AnotherClass)
        self.assertEquals(AnotherClass, value.__class__)
        self.assertEquals(SomeClass, value.some_class.__class__)
        self.assertEquals(more_classes, value.more_classes.__class__)
        self.assertEquals(MoreStuff, value.more_classes.arbitrarily_defined.__class__)
        self.assertEquals(SomeClass, value.more_classes.arbitrarily_defined.some_class.__class__)
        self.assertEquals(2, value.more_classes.arbitrarily_defined.age)

    def test_module_import(self):
        self.di.add_modules(test_module)
        with_module = self.di.build(RequiresSubModule)
        self.assertEquals(test_module.another_module.AnotherModuleClass, with_module.another_module_class.__class__)

    def test_additional_config(self):
        self.di.add_additional_configs(MoreAdditionalConfig)
        awesome = self.di.build('really_awesome_stuff')
        self.assertEquals('hey', awesome.blahblah)
        self.assertEquals(SomeClass, awesome.some_class.__class__)

    def test_circular(self):
        self.di.add_classes([Circular, WillBeCircular])
        with self.assertRaises(ValueError) as context:
            self.di.build(Circular)
        self.assertEquals(
            "Circular dependencies detected while building 'Circular' because 'Circular " + \
                "is a dependency of both 'WillBeCircular' and itself",
            str(context.exception)
        )
