import unittest
from unittest.mock import MagicMock, call
from .hsts import Hsts


class HstsTest(unittest.TestCase):
    def test_no_sub_domain(self):
        hsts = Hsts()
        input_output = type(
            "",
            (),
            {
                "set_header": MagicMock(),
            },
        )
        hsts.set_headers_for_input_output(input_output)
        input_output.set_header.assert_called_with("strict-transport-security", "max-age=31536000 ;")

    def test_sub_domain(self):
        hsts = Hsts(max_age=3600, include_sub_domains=True)
        input_output = type(
            "",
            (),
            {
                "set_header": MagicMock(),
            },
        )
        hsts.set_headers_for_input_output(input_output)
        input_output.set_header.assert_called_with("strict-transport-security", "max-age=3600 ; includeSubDomains")
