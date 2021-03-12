import unittest
from .select import Select


class SelectTest(unittest.TestCase):
    def test_check_input_bad(self):
        select = Select()
        select.configure('status', {'values': ['hey', 'bob']}, SelectTest)
        error = select.input_errors('model', {'status': 'cool'})
        self.assertEquals({'status': 'Invalid value for status'}, error)

    def test_check_input_good(self):
        select = Select()
        select.configure('status', {'values': ['hey', 'bob']}, SelectTest)
        self.assertEquals({}, select.input_errors('model', {'status': 'hey'}))
        self.assertEquals({}, select.input_errors('model', {'status': ''}))
        self.assertEquals({}, select.input_errors('model', {'status': None}))
        self.assertEquals({}, select.input_errors('model', {}))
