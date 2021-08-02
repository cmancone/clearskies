import unittest
from .json import JSON


class JSONTest(unittest.TestCase):
    def test_from_backend(self):
        json = JSON()
        self.assertDictEqual({'name': 'Bob', 'age': 5}, json.from_backend('{"name":"Bob","age":5}'))

    def test_to_backend(self):
        json = JSON()
        json.configure('some_data', {}, JSON)
        for_database = json.to_backend({
            'some_data': {'peeps': [1, 2, 3], 'more_peeps': "okay"},
            'more_data': {'okay': 'hey'},
        })
        self.assertEquals('{"peeps": [1, 2, 3], "more_peeps": "okay"}', for_database['some_data'])
        self.assertDictEqual({"okay":"hey"}, for_database['more_data'])
