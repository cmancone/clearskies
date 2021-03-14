import unittest
from .email import Email


class EmailTest(unittest.TestCase):
    def test_check_search_value(self):
        email = Email()
        email.configure('email', {}, EmailTest)
        self.assertEquals('', email.check_search_value('cmancone@example.com'))
        self.assertEquals('Invalid email address', email.check_search_value('cmancone'))
        self.assertEquals('Value must be a string for email', email.check_search_value(5))
