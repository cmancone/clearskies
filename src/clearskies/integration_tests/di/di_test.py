import unittest
from clearskies.di import Di, AdditionalConfig
import datetime

class SomeClass:
    def __init__(self, my_value: int):
        self.my_value = my_value

class MyClass:
    def __init__(self, some_specific_value: int, some_class: SomeClass):
        self.final_value = some_specific_value*some_class.my_value

class VeryNeedy:
    def __init__(self, my_class, some_other_value: str):
        self.my_class = my_class
        self.some_other_value = some_other_value

class MyOtherProvider(AdditionalConfig):
    def provide_some_specific_value(self):
        return 10

class MyProvider(AdditionalConfig):
    def provide_some_specific_value(self):
        return 5

    def can_build_class(self, class_to_check: type) -> bool:
        return class_to_check == SomeClass

    def build_class(self, class_to_provide: type, argument_name: str, di, context: str = ""):
        if class_to_provide == SomeClass:
            return SomeClass(5)
        raise ValueError(f"I was asked to build a class I didn't expect '{class_to_provide.__name__}'")

def my_function(this_uses_type_hinting_exclusively: VeryNeedy):
    return f"Jane owns {this_uses_type_hinting_exclusively.my_class.final_value} {this_uses_type_hinting_exclusively.some_other_value}s"


class DiTest(unittest.TestCase):
    def test_di_class_examples(self):
        di = Di(
            classes=[MyClass, VeryNeedy, SomeClass],
            additional_configs=[MyProvider(), MyOtherProvider()],
            bindings={
                "some_other_value": "dog",
            },
        )

        assert di.call_function(my_function) == "Jane owns 50 dogs"

    def test_add_classes_example(self):
        class MyClass:
            name = "Simple Demo"

        def my_function(my_class):
            return my_class.name

        di = Di(classes=[MyClass])
        assert "Simple Demo" == di.call_function(my_function)

        di = Di()
        di.add_classes(MyClass)
        assert "Simple Demo" == di.call_function(my_function)

    def test_add_modules_example(self):
        from . import my_module

        def my_function(my_class):
            return my_class.count

        di = Di(modules=my_module)
        assert di.call_function(my_function) == 5

        di = Di()
        di.add_modules([my_module])
        assert di.call_function(my_function) == 5

    def test_add_additional_config(self):
        class MyConfig(AdditionalConfig):
            def provide_some_value(self):
                return 2

            def provide_another_value(self, some_value):
                return some_value*2

        def my_function(another_value):
            return another_value

        di = Di()
        di.add_additional_configs([MyConfig()])
        assert di.call_function(my_function) == 4

        di = Di(additional_configs=[MyConfig()])
        assert di.call_function(my_function) == 4

    def test_add_binding(self):
        def my_function(my_name):
            return my_name

        di = Di()
        di.add_binding("my_name", 12345)
        assert di.call_function(my_function) == 12345

        di = Di(bindings={"my_name": 12345})
        assert di.call_function(my_function) == 12345

    def test_add_class_override(self):
        class TypeHintedClass:
            my_value = 5

        class ReplacementClass:
            my_value = 10

        di = Di()
        di.add_classes(TypeHintedClass)
        di.add_class_override(TypeHintedClass, ReplacementClass)

        def my_function(some_value: TypeHintedClass):
            return some_value.my_value

        assert di.call_function(my_function) == 10

        di = Di(classes=[TypeHintedClass], class_overrides={TypeHintedClass: ReplacementClass})
        assert di.call_function(my_function) == 10

    def test_now(self):
        di = Di()
        now = datetime.datetime.now()
        also_now = di.build("now")
        assert now.year == also_now.year
        assert now.month == also_now.month
        assert now.day == also_now.day
        assert also_now.tzinfo == None

        di.set_now(now)
        assert now == di.build("now")
        assert now != also_now

    def test_utcnow(self):
        di = Di()
        utcnow = datetime.datetime.now(datetime.timezone.utc)
        also_utcnow = di.build("utcnow")
        assert utcnow.year == also_utcnow.year
        assert utcnow.month == also_utcnow.month
        assert utcnow.day == also_utcnow.day
        assert also_utcnow.tzinfo == datetime.timezone.utc

        di.set_utcnow(utcnow)
        assert utcnow == di.build("utcnow")
        assert utcnow != also_utcnow
