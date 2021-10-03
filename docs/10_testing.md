# Testing

clearskies doesn't have any opinion about testing frameworks.  It works fine with the standard python test suite, and it should integrate well with any other testing tools as well.  There are two main strategies for testing clearskies applications:

 1. For unit tests, you can manually construct your classes dependencies and inject them directly
 2. You can also use the test context to execute applications/handlers/functions

## Manual Testing

There isn't too much to say here.  For simpler classes without complicated dependencies, you can always just build your own dependencies and test as desired:

```
import datetime
import unittest

def current_time_as_string(now):
    return str(now)

class TestConversion(unittest.TestCase):
    def test_conversion(self):
        converted = current_time_as_string(datetime.datetime(year=2021, month=10, day=3))
        self.assertEqual('2021-10-03 00:00:00', converted)

if __name__ == '__main__':
    unittest.main()
```

## Test Context

The test context is [a context](./5_handlers.md) intended for testing.  Like any other context, it can execute applications, handlers, and functions directly.  You can specify input for the call and also fetch any output from the execution.  Also like any other context, you can override dependency injection configuration at run-time, allowing you to fully control how your code runs.  As a simple example, here is how you would execute the simple `current_time_as_string` function above using the test context:

```
import datetime
import unittest
import clearskies

def current_time_as_string(now):
    return str(now)

class TestConversion(unittest.TestCase):
    def test_conversion(self):
        convert_test = clearskies.contexts.test(current_time_as_string)
        convert_test.bind('now', datetime.datetime(year=2021, month=10, day=3))
        converted = convert_test()
        self.assertEqual('2021-10-03 00:00:00', converted[0])

if __name__ == '__main__':
    unittest.main()
```

Obviously, for simple cases like this, there isn't much benefit to using the test context.  However, this is quite helpful for larger applications or situations where you have a more complicated dependency injection tree.  It can especially be useful for models, since then you have to start worrying about backends.

For integration tests, it's common practice to point your tests towards a database which is a clone of the production database, and clear/reset the database between each test.  You can do this with clearskies of course (by adjusting the cursor backend however you want), but another option is to swap your backend out for a memory backend.  This should generally work for _any_ backend.  Here's an example of a model, function, and test that uses the memory backend like this:

```
import datetime
import unittest
import clearskies
import json
from collections import OrderedDict

class Widget(clearskies.Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            clearskies.column_types.string('name'),
            clearskies.column_types.integer('length'),
            clearskies.column_types.integer('width'),
            clearskies.column_types.integer('height'),
            clearskies.column_types.created('created'),
            clearskies.column_types.updated('updated'),
        ])

class Widgets(clearskies.Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def model_class(self):
        return Widget

def get_my_widgets(widgets):
    matching_widgets = widgets.where('length<10').where('width<10').where('height<10').sort_by('name', 'asc')
    return [
        {'name': widget.name, 'volume': widget.length*widget.width*widget.height}
        for widget
        in matching_widgets
    ]

class TestMyWidgets(unittest.TestCase):
    def setUp(self):
        # wrap our callable in a test context
        self.my_widgets = clearskies.contexts.test(
            get_my_widgets,
            binding_classes=[Widget, Widgets],
        )

        # the test context automatically creates a memory backend and replaces the cursor backend
        self.my_widgets.memory_backend

        # it can also build dependencies for us, so let's grab the widgets object and make some widgets
        widgets = self.my_widgets.build(Widgets)
        widgets.create({'name': 'just right', 'length': 1, 'width': 1, 'height': 1})
        widgets.create({'name': 'too long', 'length': 15, 'width': 5, 'height': 5})
        widgets.create({'name': 'good enough', 'length': 5, 'width': 5, 'height': 5})

    def test_my_widgets(self):
        # execute the callable through the context
        results = self.my_widgets()
        self.assertEqual(
            [
                {"name": "good enough", "volume": 125},
                {"name": "just right", "volume": 1}
            ],
            json.loads(results[0])
        )


if __name__ == '__main__':
    unittest.main()
```
