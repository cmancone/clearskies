import unittest
from clearskies.di import Di, AdditionalConfig

class SomeClass:
    def __init__(self, my_value: int):
        self.my_value = my_value

class MyClass:
    def __init__(self, some_specific_value: int, some_class: SomeClass):
        self.final_value = some_specific_value*some_class.my_value

class VeryNeedy:
    def __init__(self, my_class, some_other_value):
        self.my_class = MyClass
        self.some_other_value = some_other_value

class MyOtherProvider(AdditionalConfig):
    def provide_some_specific_value(self):
        return 10

class MyProvider(AdditionalConfig):
    def provide_some_specific_value(self):
        return 5

    def can_provide_class(self, class_to_check: type) -> bool:
        return class_to_check == SomeClass

    def provide_class(self, class_to_provide: type):
        if class_to_provide == SomeClass:
            return SomeClass(5)
        raise ValueError(f"I was asked to build a class I didn't expect '{class_to_provide.__name__}'")

def my_function(this_uses_type_hinting_exclusively: VeryNeedy):
    return f"Jane owns {this_uses_type_hinting_exclusively.my_class.final_value}: {this_uses_type_hinting_exclusively.some_other_value}s"


class DiTest(unittest.TestCase):
    def test_di_class_examples(self):
        di = Di(
            classes=[MyClass],
            additional_configs=[MyProvider(), MyOtherProvider()],
            bindings={
                "some_other_value": "dogs",
            },
        )

        assert "Jane owns 50 dogs"
