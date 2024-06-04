import unittest
from .phone import Phone
from unittest.mock import MagicMock


class PhoneTest(unittest.TestCase):
    def test_to_backend(self):
        phone = Phone("di")
        phone.configure("phone", {}, int)
        data = phone.to_backend({"phone": "+1 (555) 123-4567"})
        self.assertEqual("15551234567", data["phone"])

    def test_input_error_for_value(self):
        phone = Phone("di")
        phone.configure("phone", {}, int)
        self.assertEqual("", phone.input_error_for_value("+1 (555) 123-4567"))
        self.assertEqual("", phone.input_error_for_value("1(555)1234567"))
        self.assertEqual("", phone.input_error_for_value("21(555)1234567"))
        self.assertEqual("Invalid phone number", phone.input_error_for_value("1(555)1234567a"))
        self.assertEqual("Invalid phone number", phone.input_error_for_value("155512345675165165165"))

    def test_input_error_for_usa_value(self):
        phone = Phone("di")
        phone.configure("phone", {"usa_only": True}, int)
        self.assertEqual("", phone.input_error_for_value("+1 (555) 123-4567"))
        self.assertEqual("", phone.input_error_for_value("1(555)1234567"))
        self.assertEqual("", phone.input_error_for_value("(555)1234567"))
        self.assertEqual("Invalid phone number", phone.input_error_for_value("21(555)1234567"))
        self.assertEqual("Invalid phone number", phone.input_error_for_value("1(555)1234567a"))
        self.assertEqual("Invalid phone number", phone.input_error_for_value("155512345678"))
        self.assertEqual("Invalid phone number", phone.input_error_for_value("1555123456"))
