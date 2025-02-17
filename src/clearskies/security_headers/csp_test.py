import unittest
from unittest.mock import MagicMock, call
from .csp import Csp


class CSPTest(unittest.TestCase):
    def test_a_bunch(self):
        csp = Csp(img_src="self", default_src="self")
        response_headers = MagicMock()
        response_headers.add = MagicMock()
        input_output = type(
            "",
            (),
            {
                "response_headers": response_headers,
            },
        )
        csp.set_headers_for_input_output(input_output)
        input_output.response_headers.add.assert_called_with("content-security-policy", "default-src 'self'; img-src 'self'")
