import unittest
from unittest.mock import MagicMock, call

from .hsts import Hsts


class HstsTest(unittest.TestCase):
    def test_no_sub_domain(self):
        hsts = Hsts()
        response_headers = MagicMock()
        response_headers.add = MagicMock()
        input_output = type(
            "",
            (),
            {
                "response_headers": response_headers,
            },
        )
        hsts.set_headers_for_input_output(input_output)
        input_output.response_headers.add.assert_called_with("strict-transport-security", "max-age=31536000 ;")

    def test_sub_domain(self):
        hsts = Hsts(max_age=3600, include_sub_domains=True)
        response_headers = MagicMock()
        response_headers.add = MagicMock()
        input_output = type(
            "",
            (),
            {
                "response_headers": response_headers,
            },
        )
        hsts.set_headers_for_input_output(input_output)
        input_output.response_headers.add.assert_called_with(
            "strict-transport-security", "max-age=3600 ; includeSubDomains"
        )
