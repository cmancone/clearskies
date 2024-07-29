import unittest
from .email import Email


class EmailTest(unittest.TestCase):
    def test_check_search_value(self):
        email = Email("di")
        email.configure("email", {}, EmailTest)
        self.assertEqual("", email.check_search_value("cmancone@example.com"))
        self.assertEqual("Invalid email address", email.check_search_value("cmancone"))
        self.assertEqual("Value must be a string for email", email.check_search_value(5))
